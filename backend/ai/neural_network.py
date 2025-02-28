import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

class ArbitragePredictor(tf.keras.Model):
    def __init__(self, sequence_length=100, n_features=10):
        super().__init__()
        self.sequence_length = sequence_length
        self.n_features = n_features
        
        # LSTM layers for temporal pattern recognition
        self.lstm1 = LSTM(128, return_sequences=True)
        self.lstm2 = LSTM(64, return_sequences=False)
        
        # Dense layers for decision making
        self.dense1 = Dense(32, activation='relu')
        self.dropout = Dropout(0.2)
        self.dense2 = Dense(16, activation='relu')
        self.output_layer = Dense(3, activation='softmax')  # Buy, Sell, Hold
        
    def call(self, inputs):
        x = self.lstm1(inputs)
        x = self.lstm2(x)
        x = self.dense1(x)
        x = self.dropout(x)
        x = self.dense2(x)
        return self.output_layer(x)
    
    def train_step(self, data):
        x, y = data
        
        with tf.GradientTape() as tape:
            y_pred = self(x, training=True)
            loss = self.compiled_loss(y, y_pred)
            
        gradients = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        self.compiled_metrics.update_state(y, y_pred)
        
        return {m.name: m.result() for m in self.metrics}

class ReinforcementLearner:
    def __init__(self, state_size, action_size, learning_rate=0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = []
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        self.model = self._build_model()
        
    def _build_model(self):
        model = tf.keras.Sequential([
            Dense(64, input_dim=self.state_size, activation='relu'),
            Dense(32, activation='relu'),
            Dense(self.action_size, activation='linear')
        ])
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.randint(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])
    
    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        
        minibatch = np.random.choice(self.memory, batch_size, replace=False)
        states = np.array([i[0] for i in minibatch])
        actions = np.array([i[1] for i in minibatch])
        rewards = np.array([i[2] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])
        dones = np.array([i[4] for i in minibatch])
        
        targets = rewards + self.gamma * np.amax(self.model.predict(next_states), axis=1) * (1 - dones)
        target_f = self.model.predict(states)
        
        for i, action in enumerate(actions):
            target_f[i][action] = targets[i]
        
        self.model.fit(states, target_f, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class ArbitrageEnvironment:
    def __init__(self, initial_balance=1000):
        self.initial_balance = initial_balance
        self.reset()
        
    def reset(self):
        self.balance = self.initial_balance
        self.position = None
        self.entry_price = None
        return self._get_state()
    
    def step(self, action, market_data):
        # Action: 0 = Hold, 1 = Buy, 2 = Sell
        reward = 0
        done = False
        
        current_price = market_data['price']
        
        if action == 1 and self.position is None:  # Buy
            self.position = self.balance / current_price
            self.entry_price = current_price
            reward = -market_data['transaction_cost']
        
        elif action == 2 and self.position is not None:  # Sell
            profit = self.position * (current_price - self.entry_price)
            reward = profit - market_data['transaction_cost']
            self.balance += profit
            self.position = None
            self.entry_price = None
        
        if self.balance <= 0:
            done = True
            reward = -1
        
        return self._get_state(), reward, done
    
    def _get_state(self):
        return {
            'balance': self.balance,
            'position': self.position,
            'entry_price': self.entry_price
        }
