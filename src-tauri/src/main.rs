// ZPix Tauri v2 — Native app wrapper with Python sidecar
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::Stdio;
use std::time::Duration;
use tauri::{Emitter, Manager};
use tokio::time::sleep;

/// Resolve the project root directory containing start-mac.sh.
/// Works both in dev (repo root) and in .app bundle.
fn resolve_app_dir() -> Option<PathBuf> {
    // Strategy 1: from current_exe (dev: target/release/zpix → 3× parent = repo root)
    if let Ok(exe) = std::env::current_exe() {
        for ancestor in [3, 4] {
            if let Some(dir) = exe.ancestors().nth(ancestor) {
                if dir.join("start-mac.sh").exists() {
                    return Some(dir.to_path_buf());
                }
            }
        }
    }
    // Strategy 2: current working dir
    if let Ok(dir) = std::env::current_dir() {
        if dir.join("start-mac.sh").exists() {
            return Some(dir);
        }
    }
    None
}

#[tauri::command]
async fn start_python_sidecar(app: tauri::AppHandle) -> Result<String, String> {
    let app_dir = resolve_app_dir().ok_or("Cannot locate project root (start-mac.sh not found)")?;
    let script_path = app_dir.join("start-mac.sh");

    // Set model cache to app data dir so it's preserved across updates
    let cache_dir: PathBuf = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("App data dir error: {}", e))?
        .join("models");
    std::fs::create_dir_all(&cache_dir).ok();

    // Detect offline mode (no internet = use cached models only)
    let offline = !is_online().await;
    if offline {
        app.emit("gradioprogress", "Offline mode — using cached models")
            .ok();
    }

    let mut cmd = std::process::Command::new("bash");
    cmd.arg(&script_path)
        .env("PORT", "7860")
        .env("HF_HOME", &cache_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    if offline {
        cmd.env("ZPIX_OFFLINE", "1");
    }

    // Create new process group so we can kill the whole tree (bash + Python grandchildren)
    unsafe {
        cmd.pre_exec(|| {
            libc::setpgid(0, 0);
            Ok(())
        });
    }

    let child = cmd
        .spawn()
        .map_err(|e| format!("Failed to spawn start-mac.sh: {}", e))?;

    let pgid = child.id() as i32;
    app.state::<SidecarState>().set(child, pgid);

    // Poll Gradio health endpoint
    let client = reqwest::Client::new();
    for attempt in 1..=60 {
        sleep(Duration::from_secs(1)).await;
        match client.get("http://127.0.0.1:7860").send().await {
            Ok(resp) if resp.status().is_success() => {
                app.emit("gradioready", "http://127.0.0.1:7860")
                    .map_err(|e| e.to_string())?;
                return Ok("Gradio ready".into());
            }
            _ => {
                if attempt % 10 == 0 {
                    app.emit(
                        "gradioprogress",
                        format!("Waiting for Gradio... ({}/60)", attempt),
                    )
                    .ok();
                }
            }
        }
    }

    Err("Gradio did not start within 60 seconds".into())
}

async fn is_online() -> bool {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(3))
        .build()
        .unwrap_or_else(|_| reqwest::Client::new());
    client
        .head("https://huggingface.co")
        .send()
        .await
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}

struct SidecarState {
    child: std::sync::Mutex<Option<std::process::Child>>,
    pgid: std::sync::Mutex<i32>,
}

impl SidecarState {
    fn new() -> Self {
        Self {
            child: std::sync::Mutex::new(None),
            pgid: std::sync::Mutex::new(0),
        }
    }
    fn set(&self, child: std::process::Child, pgid: i32) {
        let mut lock = self.child.lock().unwrap();
        *lock = Some(child);
        let mut pgid_lock = self.pgid.lock().unwrap();
        *pgid_lock = pgid;
    }
    fn kill_group(&self) {
        let pgid = *self.pgid.lock().unwrap();
        if pgid > 0 {
            unsafe {
                libc::kill(-pgid, libc::SIGTERM);
            }
        }
        if let Ok(mut lock) = self.child.lock() {
            if let Some(mut child) = lock.take() {
                let _ = child.kill();
            }
        }
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState::new())
        .invoke_handler(tauri::generate_handler![start_python_sidecar])
        .setup(|app| {
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_python_sidecar(app_handle).await {
                    eprintln!("Sidecar error: {}", e);
                }
            });
            Ok(())
        })
        .on_window_event(|app, event| {
            if let tauri::WindowEvent::Destroyed = event {
                app.state::<SidecarState>().kill_group();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
