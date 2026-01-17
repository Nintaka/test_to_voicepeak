import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import sounddevice as sd
import soundfile as sf
import os
import sys

# 必要なライブラリ: pip install sounddevice soundfile numpy

class VoicepeakDiscordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VOICEPEAK Transmit (Monitor & Emotions)")
        self.root.geometry("600x700") # スライダーとモニター設定の分、少し縦長に
        
        # --- 変数初期化 ---
        # ユーザー指定のパスを優先、無ければCドライブ等を探す
        default_path = "E:/VOICEPEAK/voicepeak.exe"
        if not os.path.exists(default_path):
            default_path = "C:/Program Files/VOICEPEAK/voicepeak.exe"

        self.voicepeak_path = tk.StringVar(value=default_path)
        
        # デバイス選択用
        self.selected_device_name = tk.StringVar()
        self.monitor_device_name = tk.StringVar()
        self.use_monitor = tk.BooleanVar(value=True) # デフォルトON
        
        self.narrator_name = tk.StringVar()
        self.status_var = tk.StringVar(value="待機中")
        self.input_text = tk.StringVar()
        
        self.device_map = {}
        self.emotion_vars = {} # {感情名: IntVar, ...}
        
        # --- UI構築 ---
        self._create_widgets()
        
        # --- イベントバインド ---
        self.narrator_combo.bind("<<ComboboxSelected>>", self._on_narrator_changed)
        
        # --- 初期化処理 ---
        self.root.after(500, self._refresh_device_list)
        self.root.after(800, self._refresh_narrator_list)

    def _create_widgets(self):
        # 1. 設定セクション
        config_frame = tk.LabelFrame(self.root, text=" 設定 / Configuration ", padx=10, pady=10)
        config_frame.pack(fill="x", padx=15, pady=10)
        
        # VOICEPEAK Path
        path_frame = tk.Frame(config_frame)
        path_frame.pack(fill="x", pady=5)
        tk.Label(path_frame, text="VOICEPEAKパス:", width=15, anchor="w").pack(side="left")
        tk.Entry(path_frame, textvariable=self.voicepeak_path).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(path_frame, text="参照...", command=self._browse_file, width=8).pack(side="left")

        # Output Device (Transmit)
        device_frame = tk.Frame(config_frame)
        device_frame.pack(fill="x", pady=5)
        tk.Label(device_frame, text="送信先デバイス:", width=15, anchor="w").pack(side="left")
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.selected_device_name, state="readonly")
        self.device_combo.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(device_frame, text="更新", command=self._refresh_device_list, width=8).pack(side="left")

        # Monitor Device (自分用)
        monitor_frame = tk.Frame(config_frame)
        monitor_frame.pack(fill="x", pady=5)
        tk.Checkbutton(monitor_frame, text="自分でも聞く:", variable=self.use_monitor, width=13, anchor="w").pack(side="left")
        self.monitor_combo = ttk.Combobox(monitor_frame, textvariable=self.monitor_device_name, state="readonly")
        self.monitor_combo.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(monitor_frame, text="", width=8).pack(side="left") # スペース合わせ

        # Narrator
        narrator_frame = tk.Frame(config_frame)
        narrator_frame.pack(fill="x", pady=5)
        tk.Label(narrator_frame, text="ナレーター名:", width=15, anchor="w").pack(side="left")
        self.narrator_combo = ttk.Combobox(narrator_frame, textvariable=self.narrator_name, state="readonly")
        self.narrator_combo.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(narrator_frame, text="取得", command=self._refresh_narrator_list, width=8).pack(side="left")

        # 2. 感情調整セクション
        self.emotion_frame_container = tk.LabelFrame(self.root, text=" 感情調整 / Emotions ", padx=10, pady=10)
        self.emotion_frame_container.pack(fill="x", padx=15, pady=5)
        
        self.sliders_frame = tk.Frame(self.emotion_frame_container)
        self.sliders_frame.pack(fill="x")
        
        tk.Button(self.emotion_frame_container, text="感情リセット", command=self._reset_emotions, font=("", 8)).pack(anchor="e", pady=2)

        # 3. メッセージ入力セクション
        main_frame = tk.LabelFrame(self.root, text=" メッセージ入力 / Message ", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.text_entry = tk.Entry(main_frame, textvariable=self.input_text, font=("", 12))
        self.text_entry.pack(fill="x", pady=10)
        self.text_entry.bind("<Return>", self.on_send)
        
        self.send_btn = tk.Button(main_frame, text="送信して再生 (Send & Play)", command=self.on_send, bg="#e1e1e1", pady=5)
        self.send_btn.pack(fill="x")
        
        # 4. ステータスバー
        status_frame = tk.Frame(self.root, relief="sunken", bd=1, padx=5, pady=2)
        status_frame.pack(side="bottom", fill="x")
        tk.Label(status_frame, text="Status:", width=8, anchor="w").pack(side="left")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, fg="#005fb8", font=("", 9, "bold"))
        self.status_label.pack(side="left", fill="x", expand=True, anchor="w")

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select VOICEPEAK Executable",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if path:
            self.voicepeak_path.set(path)

    def _refresh_device_list(self):
        """デバイス一覧更新（送信先とモニター用）"""
        try:
            devices = sd.query_devices()
            self.device_map = {}
            display_list = []
            
            for i, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    api_name = sd.query_hostapis(dev['hostapi'])['name']
                    display_name = f"{dev['name']} [{api_name}]"
                    self.device_map[display_name] = i
                    display_list.append(display_name)
            
            self.device_combo['values'] = display_list
            self.monitor_combo['values'] = display_list
            
            if display_list:
                # 送信先 (CABLE Input優先)
                current = self.selected_device_name.get()
                if current in display_list:
                    self.device_combo.set(current)
                else:
                    default_sel = display_list[0]
                    for name in display_list:
                        if "CABLE Input" in name:
                            default_sel = name
                            break
                    self.device_combo.set(default_sel)
                
                # モニター (現在の設定 or スピーカー優先)
                current_mon = self.monitor_device_name.get()
                if current_mon in display_list:
                    self.monitor_combo.set(current_mon)
                else:
                    default_mon = sd.query_devices(kind='output')['name']
                    found = False
                    for name in display_list:
                        if default_mon in name:
                            self.monitor_combo.set(name)
                            found = True
                            break
                    if not found and display_list:
                        self.monitor_combo.set(display_list[0])
                        
        except Exception as e:
            messagebox.showerror("Error", f"Audio device error: {e}")

    def _refresh_narrator_list(self):
        """ナレーター一覧取得"""
        exe = self.voicepeak_path.get()
        if not os.path.exists(exe): return

        try:
            self.root.config(cursor="wait")
            startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
            if startupinfo: startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run([exe, "--list-narrator"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            
            if proc.returncode == 0:
                raw = proc.stdout.strip().split('\n')
                narrators = [x.strip() for x in raw if x.strip()]
                self.narrator_combo['values'] = narrators
                
                # 宮舞モカ等の優先選択
                if narrators and not self.narrator_name.get():
                    target = narrators[0]
                    for n in narrators:
                        if "宮舞" in n or "Moca" in n:
                            target = n
                            break
                    self.narrator_combo.set(target)
                    self._update_emotion_sliders(target)
            else:
                print(f"Narrator fetch failed: {proc.stderr}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.root.config(cursor="")

    def _on_narrator_changed(self, event):
        narrator = self.narrator_name.get()
        if narrator:
            self._update_emotion_sliders(narrator)

    def _update_emotion_sliders(self, narrator):
        """感情スライダーの再生成"""
        exe = self.voicepeak_path.get()
        
        for widget in self.sliders_frame.winfo_children():
            widget.destroy()
        self.emotion_vars = {}

        try:
            startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
            if startupinfo: startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run([exe, "--list-emotion", narrator], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            
            if proc.returncode == 0:
                emotions = [e.strip() for e in proc.stdout.strip().split('\n') if e.strip()]
                
                if not emotions:
                    tk.Label(self.sliders_frame, text="このナレーターには感情パラメータがありません", fg="gray").pack()
                
                for i, emo_name in enumerate(emotions):
                    row = i // 2
                    col = i % 2
                    frame = tk.Frame(self.sliders_frame, padx=5, pady=2)
                    frame.grid(row=row, column=col, sticky="ew")
                    
                    lbl = tk.Label(frame, text=emo_name, width=12, anchor="w", font=("", 9))
                    lbl.pack(side="left")
                    
                    val_var = tk.IntVar(value=0)
                    self.emotion_vars[emo_name] = val_var
                    
                    scale = tk.Scale(frame, from_=0, to=100, orient="horizontal", variable=val_var, length=120, showvalue=True)
                    scale.pack(side="left", fill="x", expand=True)
            else:
                tk.Label(self.sliders_frame, text="感情取得不可").pack()
        except Exception:
            pass

    def _reset_emotions(self):
        for var in self.emotion_vars.values():
            var.set(0)

    def on_send(self, event=None):
        text = self.input_text.get().strip()
        if not text: return
        
        self._set_busy_state(True)
        
        # 感情パラメータ収集
        emotions_args = []
        for name, var in self.emotion_vars.items():
            val = var.get()
            if val > 0:
                emotions_args.extend(["-e", f"{name}={val}"])

        threading.Thread(target=self._process_pipeline, args=(text, emotions_args), daemon=True).start()

    def _set_busy_state(self, busy):
        if busy:
            self.send_btn.config(state="disabled")
            self.text_entry.config(state="disabled")
            self.root.config(cursor="wait")
        else:
            self.send_btn.config(state="normal")
            self.text_entry.config(state="normal")
            self.text_entry.delete(0, tk.END)
            self.text_entry.focus_set()
            self.root.config(cursor="")

    def _process_pipeline(self, text, emotion_args):
        temp_file = "temp_voice.wav"
        try:
            exe_path = self.voicepeak_path.get()
            narrator = self.narrator_name.get()
            device_name = self.selected_device_name.get()
            monitor_name = self.monitor_device_name.get()
            do_monitor = self.use_monitor.get()
            
            if not os.path.exists(exe_path):
                raise FileNotFoundError(f"Path invalid: {exe_path}")
            
            if device_name not in self.device_map:
                raise ValueError("Output device not selected.")
            
            device_id = self.device_map[device_name]
            monitor_id = self.device_map.get(monitor_name)
            
            self.status_var.set("生成中...")
            
            # コマンド作成
            cmd = [exe_path, "-s", text, "-o", temp_file]
            if narrator:
                cmd.extend(["-n", narrator])
            cmd.extend(emotion_args)
            
            startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
            if startupinfo: startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo
            )
            
            if proc.returncode != 0:
                raise RuntimeError(f"VOICEPEAK Error:\n{proc.stderr}")
            
            if not os.path.exists(temp_file):
                raise RuntimeError("Output file missing.")

            self.status_var.set(f"再生中...")
            
            # --- 同時再生ロジック ---
            data, fs = sf.read(temp_file, dtype='float32')
            channels = data.shape[1] if len(data.shape) > 1 else 1

            def play_worker(dev_id):
                try:
                    with sd.OutputStream(device=dev_id, samplerate=fs, channels=channels) as stream:
                        stream.write(data)
                except Exception as e:
                    print(f"Playback error dev {dev_id}: {e}")

            threads = []
            # 1. 送信用 (Discord)
            threads.append(threading.Thread(target=play_worker, args=(device_id,)))
            
            # 2. モニター用 (自分)
            if do_monitor and monitor_id is not None:
                threads.append(threading.Thread(target=play_worker, args=(monitor_id,)))

            for t in threads: t.start()
            for t in threads: t.join() # 全ての再生完了を待つ
            
            self.status_var.set("完了")
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.status_var.set("エラー")
        finally:
            self.root.after(0, lambda: self._set_busy_state(False))

if __name__ == "__main__":
    root = tk.Tk()
    app = VoicepeakDiscordApp(root)
    root.mainloop()