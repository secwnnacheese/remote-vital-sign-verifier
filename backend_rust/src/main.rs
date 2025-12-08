use serde::Serialize;
use std::env;
use std::f64::consts::PI;
use std::process;

#[derive(Serialize)]
struct SignalResult {
    time: Vec<f64>,
    x1: Vec<f64>,
    x2: Vec<f64>,
    y: Vec<f64>,
}

fn parse_arg<T: std::str::FromStr>(key: &str, default: T) -> T {
    let args: Vec<String> = env::args().collect();
    for window in args.windows(2) {
        if window[0] == format!("--{}", key) {
            if let Ok(val) = window[1].parse::<T>() {
                return val;
            }
        }
    }
    default
}

fn main() {
    let mode = parse_arg::<String>("mode", "add".to_string());
    let f1 = parse_arg("f1", 1.0_f64);
    let a1 = parse_arg("a1", 1.0_f64);
    let p1 = parse_arg("p1", 0.0_f64);
    let f2 = parse_arg("f2", 1.0_f64);
    let a2 = parse_arg("a2", 1.0_f64);
    let p2 = parse_arg("p2", 0.0_f64);
    let duration = parse_arg("duration", 2.0_f64);
    let dt = parse_arg("dt", 0.01_f64);

    if dt <= 0.0 || duration <= 0.0 {
        eprintln!("dt and duration must be positive");
        process::exit(1);
    }

    let n_steps = (duration / dt).ceil() as usize;
    let mut time = Vec::with_capacity(n_steps);
    let mut x1 = Vec::with_capacity(n_steps);
    let mut x2 = Vec::with_capacity(n_steps);
    let mut y = Vec::with_capacity(n_steps);

    for i in 0..n_steps {
        let t = i as f64 * dt;
        let s1 = a1 * (2.0 * PI * f1 * t + p1).sin();
        let s2 = a2 * (2.0 * PI * f2 * t + p2).sin();
        let out = match mode.as_str() {
            "sub" => s1 - s2,
            "mul" => s1 * s2,
            _ => s1 + s2,
        };
        time.push(t);
        x1.push(s1);
        x2.push(s2);
        y.push(out);
    }

    let result = SignalResult { time, x1, x2, y };
    match serde_json::to_string(&result) {
        Ok(json) => println!("{}", json),
        Err(e) => {
            eprintln!("Failed to serialize: {}", e);
            process::exit(1);
        }
    }
}
