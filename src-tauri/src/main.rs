// ZPix Tauri v2 — Native app wrapper with Python sidecar
use std::process::Stdio;
use std::time::Duration;
use tauri::{Emitter, Manager};
use tokio::time::sleep;

#[tauri::command]
async fn start_python_sidecar(app: tauri::AppHandle) -> Result<String, String> {
    let app_dir = std::env::current_dir().map_err(|e| e.to_string())?;
    let script_path = app_dir.join("start-mac.sh");

    if !script_path.exists() {
        return Err(format!("start-mac.sh not found at {:?}", script_path));
    }

    let child = std::process::Command::new("bash")
        .arg(&script_path)
        .env("PORT", "7860")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn start-mac.sh: {}", e))?;

    // Store child process in app state so we can kill it on exit
    app.state::<SidecarState>().set(child);

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
                    app.emit("gradioprogress", format!("Waiting for Gradio... ({}/60)", attempt))
                        .ok();
                }
            }
        }
    }

    Err("Gradio did not start within 60 seconds".into())
}

struct SidecarState {
    child: std::sync::Mutex<Option<std::process::Child>>,
}

impl SidecarState {
    fn new() -> Self {
        Self {
            child: std::sync::Mutex::new(None),
        }
    }
    fn set(&self, child: std::process::Child) {
        let mut lock = self.child.lock().unwrap();
        *lock = Some(child);
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
                if let Ok(mut lock) = app.state::<SidecarState>().child.lock() {
                    if let Some(mut child) = lock.take() {
                        let _ = child.kill();
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
