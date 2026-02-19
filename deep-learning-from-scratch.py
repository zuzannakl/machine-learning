import numpy as np
import matplotlib.pyplot as plt
from typing import Callable
from keras.datasets import mnist
from keras.utils import to_categorical
from tqdm import tqdm

def sigmoid(z: np.ndarray, pochodna: bool = False) -> np.ndarray:
    s = 1 / (1 + np.exp(-z))
    if pochodna:
        return s * (1 - s)
    else:
        return s

def softmax(z: np.ndarray, pochodna: bool = False) -> np.ndarray:
    e_z = np.exp(z) 
    return e_z / np.sum(e_z, axis = 1, keepdims = True)

def entropia_krzyzowa(y: np.ndarray, test: np.ndarray, pochodna: bool = False) -> float | np.ndarray:
    epsilon = 1e-15
    y = np.clip(y, epsilon, 1. - epsilon)
    return (-np.sum(test * np.log(y))) / y.shape[0]

class warstwa():
    def __init__(self, n: int, f_aktywacji: Callable|None):
        self.n = n
        self.f_aktywacji = f_aktywacji
    def inicjuj(self, rozmiar_poprzedniej: int):
        m = rozmiar_poprzedniej
        self.wagi = np.random.normal(scale = np.sqrt(6 / m), size = (m + 1, self.n))

class warstwa_wejsciowa(warstwa):
    def __init__(self, n: int):
        super().__init__(n, None)
    def inicjuj(self, rozmiar_poprzedniej: int = 0):
        pass
    def w_przod(self, wejscie: np.ndarray):
        if wejscie.shape[1] != self.n:
            raise ValueError("Wielkość wektora wejściowego jest inna niż rozmiar warstwy")
        self.a = wejscie

class warstwa_wyjsciowa(warstwa):
    def __init__(self, n: int, f_aktywacji: Callable):
        super().__init__(n, f_aktywacji)
    def w_przod(self, a_poprzedniej):
        a_pop = np.hstack([np.ones((a_poprzedniej.shape[0], 1)), a_poprzedniej])
        self.a_pop = a_pop
        self.z = a_pop @ self.wagi
        self.a = self.f_aktywacji(self.z)
    def w_tyl(self, test: np.ndarray, a_poprzedniej: np.ndarray, krok: float):
        self.pochodna_z = 1 / len(test) * (self.a - test)
        grad_w = self.a_pop.T @ self.pochodna_z
        grad_a_pop = self.pochodna_z @ self.wagi.T
        self.grad_a = grad_a_pop[:, 1:]
        self.wagi -= krok * grad_w

class warstwa_ukryta(warstwa):
    def __init__(self, n: int, f_aktywacji: Callable = sigmoid):
        super().__init__(n, f_aktywacji)
    def w_przod(self, a_poprzedniej):
        a_pop = np.hstack([np.ones((a_poprzedniej.shape[0], 1)), a_poprzedniej])
        self.a_pop = a_pop
        self.z = a_pop @ self.wagi
        self.a = self.f_aktywacji(self.z)
    def w_tyl(self, pochodna_nastepnej: np.ndarray, a_poprzedniej: np.ndarray, krok: float):
        dz = self.f_aktywacji(self.z, pochodna = True)
        self.pochodna_z = pochodna_nastepnej * dz
        grad_w = self.a_pop.T @ self.pochodna_z
        grad_a_pop = self.pochodna_z @ self.wagi.T
        self.grad_a = grad_a_pop[:, 1:]
        self.wagi -= krok * grad_w

class siec_neuronowa():
    def __init__(self, warstwy: tuple | list):
        m = warstwy[0].n
        self.warstwy = []
        for warstwa in warstwy:
            warstwa.inicjuj(m)
            self.warstwy.append(warstwa)
            m = warstwa.n
    def predict(self, x):
        a = x
        for warstwa in self.warstwy:
            warstwa.w_przod(a)
            a = warstwa.a
        return a
    def fit(self, X_train: np.ndarray, Y_train: np.ndarray,
            validation: bool = False,
            X_val: np.ndarray | None = None, Y_val: np.ndarray | None = None,
            krok: float = 1, epochs: int = 20, batch_size: int = 200, plot: bool = False,
            dynamic_step: bool = True):
        if not validation:
            X_val, Y_val = X_train, Y_train
        else:
            if X_val is None or Y_val is None:
                raise ValueError("If validation is False, X_val and Y_val are required")
        N = X_train.shape[0]
        testy = []
        for k in range(1, epochs + 1):
            if dynamic_step:
                step = krok / np.sqrt(k)
            else:
                step = krok
            U = N // batch_size
            indeksy = list(range(N))
            np.random.shuffle(indeksy)
            print(f"Epoch: {k}")
            for i in tqdm(range(U), desc = 'Postep'):
                batch_indices = indeksy[i * batch_size : (i + 1) * batch_size]
                xb = X_train[batch_indices, :]
                yb = Y_train[batch_indices, :]
                self.predict(xb)
                if len(self.warstwy) > 1:
                    self.warstwy[-1].w_tyl(yb, self.warstwy[-2].a, step)
                else:
                    pass 
                for l in range(len(self.warstwy) - 2, 0, -1):
                    grad_od_nastepnej = self.warstwy[l + 1].grad_a
                    wejscie_od_poprzedniej = self.warstwy[l - 1].a
                    self.warstwy[l].w_tyl(grad_od_nastepnej, wejscie_od_poprzedniej, step)
            y_pred_val = self.predict(X_val)
            loss_function_val = entropia_krzyzowa(y_pred_val, Y_val)
            print(f"Epoch: {k}, Loss function for validation vector: {loss_function_val:.4f}")
            if plot:
                testy.append(loss_function_val)
        if plot:
            plt.plot(np.arange(epochs), testy, ls = '-.')
            plt.title('Value of the loss function for validation vector after each epoch')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.show()

def mnist_load():
    (X_train, y_train), (X_test, y_test) = mnist.load_data()
    X_train_r = X_train.reshape(60000, 784)
    X_test_r = X_test.reshape(10000, 784)
    X_train_r = X_train_r.astype('float32')
    X_test_r = X_test_r.astype('float32')
    X_train_r /= 255                  
    X_test_r /= 255
    liczba_klas = 10
    y_train = to_categorical(y_train, liczba_klas)
    y_test = to_categorical(y_test, liczba_klas)
    return (X_train_r, y_train), (X_test_r, y_test)

def main():
    ann = siec_neuronowa([warstwa_wejsciowa(n = 784), warstwa_ukryta(n = 500),
                          warstwa_ukryta(n = 500), warstwa_ukryta(n = 500),
                          warstwa_wyjsciowa(n = 10, f_aktywacji = softmax)])
    (X_train, y_train), (X_test, y_test) = mnist_load()
    ann.fit(X_train, y_train, validation = False, krok = 0.5, epochs = 5, batch_size = 100)
    Y_pred = np.argmax(ann.predict(X_test), axis = 1)
    y_real = np.argmax(y_test, axis = 1)
    #Y_pred=ann.predict(X_test)
    #for predicted, real in zip(Y_pred,y_real):
    #    print(f'Przewidziane: {predicted}, Prawdziwe: {real}')
    lacznie = len(y_real)
    poprawne = np.sum(Y_pred == y_real)
    niepoprawne = lacznie - poprawne
    procent = (poprawne / lacznie) * 100
    print(f"do przewidzenia: {lacznie}")
    print(f"poprawnie: {poprawne}")
    print(f"niepoprawnie: {niepoprawne}")
    print(f"Skuteczność: {procent:.2f}%")
    
if __name__ == "__main__":
    main()