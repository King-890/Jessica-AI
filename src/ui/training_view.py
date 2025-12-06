from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QProgressBar, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
import sys
import os

# Redirect stdout to capture training logs
class Stream(QThread):
    new_text = pyqtSignal(str)

    def run(self):
        pass

    def write(self, text):
        self.new_text.emit(str(text))
        
    def flush(self):
        pass

class TrainingWorker(QThread):
    finished = pyqtSignal()
    
    def __init__(self, trainer, model, wrapper):
        super().__init__()
        self.trainer = trainer
        self.model = model
        self.wrapper = wrapper
        
    def run(self):
        try:
            self.trainer.fit(self.wrapper)
        except Exception as e:
            print(f"Training Error: {e}")
        self.finished.emit()

class TrainingView(QWidget):
    def __init__(self, brain, parent=None):
        super().__init__(parent)
        self.brain = brain
        self.is_training = False
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("TRAINING DASHBOARD")
        header.setStyleSheet("font-size: 24px; color: #00f3ff; font-weight: bold; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("START TRAINING")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc; color: white; border: none; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #005a9e; }
        """)
        self.start_btn.clicked.connect(self.start_training)
        
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f; color: white; border: none; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #b71c1c; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_training)
        
        self.epoch_spin = QSpinBox()
        self.epoch_spin.setRange(1, 1000)
        self.epoch_spin.setValue(10)
        self.epoch_spin.setPrefix("Epochs: ")
        self.epoch_spin.setStyleSheet("color: white; padding: 5px; background: #333;")
        
        controls_layout.addWidget(self.epoch_spin)
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.log_output)
        
        # Redirect stdout
        # Note: In a real app, intercepting stdout globally can be risky. 
        # For this demo, we'll just print to console and user can see logs there, 
        # or we try to capture specific logs.
        # Adding a manual log method instead.
        self.log_output.append(">>> Training Dashboard Ready.")
        self.log_output.append(f">>> Local Model: JessicaGPT (Vocab: {self.brain.tokenizer.vocab_size})")

    def log(self, text):
        self.log_output.append(text)

    def start_training(self):
        from src.training.dataset import DatasetBuilder
        from src.training.lightning_wrapper import TrainingModule
        import pytorch_lightning as pl
        
        self.log(">>> Initializing Training Pipeline...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.is_training = True
        
        # 1. Build Dataset
        builder = DatasetBuilder(self.brain.tokenizer)
        # Try to load collected data
        data_path = "training_data"
        import glob
        files = glob.glob(os.path.join(data_path, "*.jsonl"))
        
        if not files:
            self.log(">>> No training data found in training_data/. Using dummy RAG data.")
            dataset = builder.from_rag(self.brain.rag_manager)
        else:
            self.log(f">>> Found {len(files)} data files.")
            # Simplification: just load the first one or merge
            dataset = builder.from_jsonl(files[0]) # Load first for now
            
        self.log(f">>> Dataset size: {len(dataset)} instruction blocks.")
        
        if len(dataset) <= 0:
             self.log(">>> Error: Dataset empty. Chat with Jessica to generate data!")
             self.stop_training()
             return

        # 2. Setup Lightning
        wrapper = TrainingModule(self.brain.model, dataset, batch_size=2)
        
        # Trainer - use lightweight settings
        self.trainer = pl.Trainer(
            max_epochs=self.epoch_spin.value(),
            accelerator="auto",
            devices=1,
            enable_progress_bar=True,
            limit_train_batches=10 # Run small batches for demo speed
        )
        
        # 3. Run in Thread
        self.worker = TrainingWorker(self.trainer, self.brain.model, wrapper)
        self.worker.finished.connect(self.on_training_finished)
        self.worker.start()
        
        self.log(">>> Training Started... Check Console for Progress Bar.")

    def stop_training(self):
        # Stopping a thread forcefully is hard. 
        # In Lightning, we can set a flag but here we just update UI.
        self.log(">>> Stopping... (Wait for current epoch)")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.is_training = False

    def on_training_finished(self):
        self.log(">>> Training Completed!")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.is_training = False
        self.brain.model.eval() # Switch back to eval mode
