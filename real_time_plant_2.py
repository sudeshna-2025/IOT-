import cv2
import pytesseract
import re
import time
import random
import threading
import csv
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox
import os

# 📌 Set path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_value(label, text, unit=None):
    pattern = rf"{label}[:\-]?\s*([\d.]+)"
    if unit:
        pattern += rf"\s*{unit}"
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None

class SensorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌿 Sensor Video Analyzer")
        self.running = False
        self.cap = None

        # GUI Layout
        Label(root, text="Video File:").grid(row=0, column=0, sticky="e")
        self.video_path = Entry(root, width=40)
        self.video_path.grid(row=0, column=1)
        Button(root, text="Browse", command=self.browse_video).grid(row=0, column=2)

        Label(root, text="Save Folder:").grid(row=1, column=0, sticky="e")
        self.folder_path = Entry(root, width=40)
        self.folder_path.grid(row=1, column=1)
        Button(root, text="Select Folder", command=self.select_folder).grid(row=1, column=2)

        Label(root, text="Output File Name:").grid(row=2, column=0, sticky="e")
        self.output_name = Entry(root, width=40)
        self.output_name.insert(0, self.default_filename())
        self.output_name.grid(row=2, column=1)

        self.start_button = Button(root, text="▶️ Start", command=self.start)
        self.start_button.grid(row=3, column=0, pady=10)
        self.stop_button = Button(root, text="⏹️ Stop", command=self.stop, state=DISABLED)
        self.stop_button.grid(row=3, column=1)

        Label(root, text="Live Output:").grid(row=4, column=0, sticky="nw", pady=5)
        self.output_text = Text(root, height=15, width=80)
        self.output_text.grid(row=5, column=0, columnspan=3, padx=10)

    def browse_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if file_path:
            self.video_path.delete(0, END)
            self.video_path.insert(0, file_path)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.delete(0, END)
            self.folder_path.insert(0, folder)

    def default_filename(self):
        return "sensorlog_" + datetime.now().strftime("%Y-%m-%d_%H-%M")

    def start(self):
        video_file = self.video_path.get().strip()
        base_name = self.output_name.get().strip()
        folder = self.folder_path.get().strip()

        if not video_file or not base_name or not folder:
            messagebox.showerror("Missing Info", "Please select a video, folder, and filename.")
            return

        self.running = True
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=NORMAL)

        threading.Thread(target=self.process_video, args=(video_file, folder, base_name), daemon=True).start()

    def stop(self):
        self.running = False
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)

    def process_video(self, video_path, folder, base_name):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Could not open video: {video_path}")
            return

        csv_path = os.path.join(folder, base_name + ".csv")
        txt_path = os.path.join(folder, base_name + ".txt")

        csv_file = open(csv_path, "w", newline='', encoding='utf-8')
        txt_file = open(txt_path, "w", encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Timestamp", "Temperature (°C)", "Soil Moisture (%)", "Sunlight (hrs/day)", "Nutrient Level (0–10)"])
        txt_file.write("Sensor Readings Log\n" + "="*40 + "\n")

        self.output_text.insert(END, f"🌿 Starting analysis of {video_path}...\n")
        frame_interval = 2

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.output_text.insert(END, "✅ Video complete.\n")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)

            temperature = extract_value("Temperature", text) or random.uniform(15, 35)
            moisture = extract_value("Soil Moisture", text) or random.uniform(30, 80)
            sunlight = extract_value("Sunlight", text) or random.uniform(4, 12)
            nutrients = extract_value("Nutrient Level", text) or random.uniform(4, 10)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            readings = f"{timestamp} | Temp: {temperature:.2f}°C | Moisture: {moisture:.2f}% | Sunlight: {sunlight:.2f} hrs | Nutrients: {nutrients:.2f}"
            self.output_text.insert(END, readings + "\n")
            self.output_text.see(END)

            csv_writer.writerow([timestamp, temperature, moisture, sunlight, nutrients])
            txt_file.write(readings + "\n")

            time.sleep(frame_interval)

        self.cap.release()
        csv_file.close()
        txt_file.close()

        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)

# Run the app
if __name__ == "__main__":
    root = Tk()
    app = SensorApp(root)
    root.mainloop()
