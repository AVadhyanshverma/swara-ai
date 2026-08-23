use std::env;
use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::Command;

fn main() {
    let args: Vec<String> = env::args().collect();
    let cache_dir = dirs::cache_dir().unwrap().join("pyx");
    
    if !cache_dir.exists() {
        println!("Extracting python to cache: {:?}", cache_dir);
        fs::create_dir_all(&cache_dir).unwrap();
    }
    
    let python_bin = if cfg!(windows) {
        cache_dir.join("python").join("python.exe")
    } else {
        cache_dir.join("python").join("bin").join("python3")
    };
    
    if args.len() > 1 {
        Command::new(&python_bin)
            .args(&args[1..])
            .status()
            .unwrap_or_else(|_| std::process::ExitStatus::default());
    }
}
