"""
ex5 - Train a simple 2-layer MLP on MNIST and save outputs for SNL HLS simulation.

Network architecture (MUST match ex5/include/Network.hh):
  Input  : (28, 28, 1)  float32, normalized to [0, 1]
  Flatten: 784
  Dense  : HIDDEN_UNITS, ReLU      <- Layer0   (Network.hh Layer0 output units)
  Dense  : NUM_CLASSES,  Softmax   <- Layer1   (Network.hh Layer1 output units)

If you change HIDDEN_UNITS or NUM_CLASSES here, change the matching numbers
in ex5/include/Network.hh (Layer0 units / Layer1 units) or csim will not match.

Outputs saved to ex5/data/:
  mnist_mlp.keras    - trained model  (weights loaded by SNL testbench via --cfile)
  mnist_test.npy     - test inputs,  shape (N, 28, 28, 1) float32   (--dfile)
  mnist_golden.npy   - Keras outputs, shape (N, NUM_CLASSES) float32 (--gfile)

Run with a python that has TensorFlow/Keras, e.g. the rogue conda env:
  /sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python train_mlp.py
"""

import os

os.environ['CUDA_VISIBLE_DEVICES'] = ''  # force CPU — avoids GPU handle issues on shared nodes

import numpy as np
import tensorflow as tf
from tensorflow import keras

# ── Tunable parameters ─────────────────────────────────────────────────────────
HIDDEN_UNITS = 64      # Layer0 Dense units  (keep in sync with Network.hh Layer0)
NUM_CLASSES  = 10      # Layer1 Dense units  (keep in sync with Network.hh Layer1)
EPOCHS       = 10
BATCH_SIZE   = 128
N_SAMPLES    = 100     # how many test samples to dump for csim/cosim

# Save data next to this script (ex5/data/) regardless of the current directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ── Load MNIST ──────────────────────────────────────────────────────────────────
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

x_train = x_train.astype('float32') / 255.0
x_test  = x_test.astype('float32')  / 255.0

# Add channel dim: (N, 28, 28) -> (N, 28, 28, 1)
x_train = x_train[..., np.newaxis]
x_test  = x_test[..., np.newaxis]

print(f'Train: {x_train.shape}  Test: {x_test.shape}')

# ── Build model (must mirror Network.hh) ─────────────────────────────────────────
model = keras.Sequential([
    keras.Input(shape=(28, 28, 1)),
    keras.layers.Flatten(),
    keras.layers.Dense(HIDDEN_UNITS, activation='relu',    name='dense_0'),
    keras.layers.Dense(NUM_CLASSES,  activation='softmax', name='dense_1'),
], name='Ex5MLP')

model.summary()

# ── Train ─────────────────────────────────────────────────────────────────────
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy'],
)

model.fit(
    x_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    verbose=1,
)

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f'\nTest accuracy: {test_acc:.4f}')

# ── Save model ────────────────────────────────────────────────────────────────
model_path = os.path.join(DATA_DIR, 'mnist_mlp.keras')
model.save(model_path)
print(f'Saved: {model_path}')

# ── Save test inputs and golden outputs for csim/cosim ───────────────────────
x_samples = x_test[:N_SAMPLES].astype('float32')

test_path = os.path.join(DATA_DIR, 'mnist_test.npy')
np.save(test_path, x_samples)
print(f'Saved: {test_path}   shape={x_samples.shape}')

golden = model.predict(x_samples, verbose=0).astype('float32')
golden_path = os.path.join(DATA_DIR, 'mnist_golden.npy')
np.save(golden_path, golden)
print(f'Saved: {golden_path}  shape={golden.shape}')

print(f'Labels for first 10: {y_test[:10]}')
