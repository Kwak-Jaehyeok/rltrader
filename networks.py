import threading
import numpy as np
import tensorflow as tf
from tensorflow.keras.backend import set_session
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Input, Activation, LSTM, Dense, BatchNormalization, Dropout, Flatten
from tensorflow.keras.optimizers import SGD


lock = threading.Lock()


class Network:
    def __init__(self, input_dim=0, output_dim=0, n_steps=1, lr=0.01, shared_net=None, activation='tanh', sess=None, graph=None):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.lr = lr
        self.model = None
        self.shared_net = shared_net
        self.activation = activation
        self.sess = sess if sess is not None else tf.Session()
        self.graph = graph if graph is not None else tf.get_default_graph()

    def reset(self):
        self.prob = None

    def predict(self, sample):
        with lock:
            with self.graph.as_default():
                set_session(self.sess)
                self.prob = self.model.predict(np.array(sample).reshape((1, -1, self.input_dim))).flatten()
        return self.prob

    def train_on_batch(self, x, y):
        loss = 0.
        with lock:
            with self.graph.as_default():
                set_session(self.sess)
                loss = self.model.train_on_batch(x, y)
        return loss

    def save_model(self, model_path):
        if model_path is not None and self.model is not None:
            self.model.save_weights(model_path, overwrite=True)

    def load_model(self, model_path):
        if model_path is not None:
            self.model.load_weights(model_path)


class DNN(Network):
    def __init__(self, input_dim=0, output_dim=0, lr=0.01, shared_net=None, activation='tanh', sess=None, graph=None):
        super().__init__(
            input_dim=input_dim, 
            output_dim=output_dim, 
            lr=lr,
            shared_net=shared_net,
            activation=activation,
            sess=sess,
            graph=graph,
        )
        self.model = Sequential()
        inp = Input((1, input_dim))
        output = Dense(128, input_shape=(1, input_dim))(inp)
        output = Dropout(0.5)(output)
        output = BatchNormalization()(output)
        output = Dense(128)(output)
        output = Dropout(0.5)(output)
        output = BatchNormalization()(output)
        output = Dense(128)(output)
        output = Dropout(0.5)(output)
        output = BatchNormalization()(output)
        output = Dense(output_dim)(output)
        output = Flatten()(output)
        output = Activation(activation)(output)
        self.model.compile(optimizer=SGD(lr=lr), loss='mse')
    

class LSTMNetwork(Network):
    def __init__(self, input_dim=0, output_dim=0, n_steps=1, lr=0.01, shared_net=None, activation='tanh', sess=None, graph=None):
        super().__init__(
            input_dim=input_dim, 
            output_dim=output_dim, 
            lr=lr,
            shared_net=shared_net,
            activation=activation,
            sess=sess,
            graph=graph,
        )
        self.n_steps = n_steps
        inp = Input((self.n_steps, self.input_dim))
        output = None
        if self.shared_net is None:
            output = LSTM(256, dropout=0.1, input_shape=(n_steps, input_dim), return_sequences=True)(inp)
            output = LSTM(256, dropout=0.1, return_sequences=True)(output)
            output = LSTM(256, dropout=0.1)(output)
            output = Dense(output_dim, activation=activation)(output)
            self.model = Model(inp, output)
        else:
            output = Dense(output_dim, activation=activation)(self.shared_net.output)
            self.model = Model(self.shared_net.input, output)
        self.model.compile(optimizer=SGD(lr=lr), loss='mse')


class CNN(Network):
    pass
    

def get_shared_network(net='lstm', n_steps=1, input_dim=0):
    if net == 'lstm':
        inp = Input((n_steps, input_dim))
        output = LSTM(256, dropout=0.1, input_shape=(n_steps, input_dim), return_sequences=True)(inp)
        output = LSTM(256, dropout=0.1, return_sequences=True)(output)
        output = LSTM(256, dropout=0.1)(output)
        return Model(inp, output)
    elif net == 'dnn':
        pass