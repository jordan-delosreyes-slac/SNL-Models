"""
agent_ml_training0 - Train a 3-layer CNN on MNIST for SNL HLS.

Architecture (MUST match include/Network.hh):
  Input        : (28, 28, 1)
  Conv2D       : 8  filters, 3x3, valid, ReLU     -> (26, 26,  8)
  MaxPool2D    : 2x2, stride 2                    -> (13, 13,  8)
  Conv2D       : 16 filters, 3x3, valid, ReLU     -> (11, 11, 16)
  MaxPool2D    : 2x2, stride 2                    -> ( 5,  5, 16)
  Flatten      : 400
  Dense        : 10, Softmax

Outputs to data/:
  mnist_cnn.keras       - weights
  mnist_cnn_test.npy    - (N, 28, 28, 1) float32
  mnist_cnn_golden.npy  - (N, 10)        float32
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # force CPU

import numpy as np
import tensorflow as tf
from tensorflow import keras

# ── Tunable ────────────────────────────────────────────────────────────────────
F0           = 8      # Conv0 filters
F1           = 16     # Conv1 filters
NUM_CLASSES  = 10
EPOCHS       = 5
BATCH_SIZE   = 128
N_SAMPLES    = 100

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ── Data ───────────────────────────────────────────────────────────────────────
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
x_train = (x_train.astype('float32') / 255.0)[..., np.newaxis]
x_test  = (x_test.astype('float32')  / 255.0)[..., np.newaxis]
print(f'Train: {x_train.shape}  Test: {x_test.shape}')

# ── Model (must mirror Network.hh) ─────────────────────────────────────────────
model = keras.Sequential([
    keras.Input(shape=(28, 28, 1)),
    keras.layers.Conv2D(F0, (3, 3), strides=(1, 1), padding='valid',
                        activation='relu', name='conv_0'),
    keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2),
                              padding='valid', name='pool_0'),
    keras.layers.Conv2D(F1, (3, 3), strides=(1, 1), padding='valid',
                        activation='relu', name='conv_1'),
    keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2),
                              padding='valid', name='pool_1'),
    keras.layers.Flatten(name='flatten'),
    keras.layers.Dense(NUM_CLASSES, activation='softmax', name='dense_out'),
], name='AgentCNN')

model.summary()

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

model.fit(x_train, y_train,
          epochs=EPOCHS, batch_size=BATCH_SIZE,
          validation_split=0.1, verbose=1)

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f'\nTest accuracy: {test_acc:.4f}')

# ── Save ───────────────────────────────────────────────────────────────────────
model_path = os.path.join(DATA_DIR, 'mnist_cnn.keras')
model.save(model_path)
print(f'Saved: {model_path}')

x_samples = x_test[:N_SAMPLES].astype('float32')
test_path = os.path.join(DATA_DIR, 'mnist_cnn_test.npy')
np.save(test_path, x_samples)
print(f'Saved: {test_path}   shape={x_samples.shape}')

golden = model.predict(x_samples, verbose=0).astype('float32')
golden_path = os.path.join(DATA_DIR, 'mnist_cnn_golden.npy')
np.save(golden_path, golden)
print(f'Saved: {golden_path}  shape={golden.shape}')

print(f'Labels for first 10: {y_test[:10]}')
