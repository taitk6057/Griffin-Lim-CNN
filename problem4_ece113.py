# -*- coding: utf-8 -*-
"""Problem4 ece113.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EscuNGWcYBmiF14iRgX3bR0gjyr1nCK0

Mount your Google Drive
"""
#ECE 113 PROJECT PROBLEM 4
#TAIT KAMINSKI, DENNY TSAI, NATHAN CHEN, CHARLES BAI

from google.colab import drive
drive.mount('/content/gdrive/')

"""Change directory to working directory, change the path if this is not where you put the data."""

import os
os.chdir('/content/gdrive/My Drive/test') 
!ls

#the test folder is a seperated folder of only the first 
#100 samples to avoid out of memory error, open to anyone with link
#https://drive.google.com/drive/u/1/folders/1Wta3SOPftZ-O40NzgIwcfQHfYHnAK6Na

"""Get all audio data from .wav files

To do:
1. implement filterbanks, break up input signals into frequency bands.  You can design the filter manually or see https://scipy-cookbook.readthedocs.io/items/ButterworthBandpass.html
2. put in the best parameters for the stft found in section 1b
"""

import numpy as np
from scipy.signal import stft
from scipy.io import wavfile as wav
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt

all_files = [filename for filename in os.listdir()]
N=len(all_files)
print(all_files[0])

#we use 3 frequency bands
fs, get_audio = wav.read(all_files[0])
#stft uses optimal parameters we found from question 2
_, _, Zxx = stft(get_audio, fs, nperseg=1000, noverlap=500)

fs, get_audio = wav.read(all_files[0])
_, _, Zxx1 = stft(get_audio, fs, nperseg=1000, noverlap=500)

fs, get_audio = wav.read(all_files[0])
_, _, Zxx2 = stft(get_audio, fs, nperseg=1000, noverlap=500)

#get fed into the model
all_data=np.zeros((Zxx.shape[0]+Zxx.shape[0]%2,2*Zxx.shape[1],N))*1j
all_data1=np.zeros((Zxx1.shape[0]+Zxx1.shape[0]%2,2*Zxx1.shape[1],N))*1j
all_data2=np.zeros((Zxx2.shape[0]+Zxx2.shape[0]%2,2*Zxx2.shape[1],N))*1j

#filter banks
def butter_bandpass(lowcut, highcut, fs, order=1):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=1):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

#see report for reasoning 
fs = 16000
lowcut = 400
highcut = 7600

#3 filter bands
yf= butter_bandpass_filter(get_audio, lowcut, highcut, fs, order=1)
yf1= butter_bandpass_filter(get_audio, lowcut, highcut, fs, order=2)
yf2= butter_bandpass_filter(get_audio, lowcut, highcut, fs, order=3)

#plots just for testing/visualization/experimenting
plt.xlabel('time')
plt.plot(yf)
plt.grid()
plt.show()

plt.xlabel('time')
plt.plot(yf1)
plt.grid()
plt.show()

plt.xlabel('time')
plt.plot(yf2)
plt.grid()
plt.show()

#take stft of each band again using parameter from 2
for i in range(N):
  _, get_audio = wav.read(all_files[i])
  _, _, Zxx = stft(yf, fs, nperseg=1000, noverlap=500)
  all_data[0:Zxx.shape[0],0:Zxx.shape[1],i]=Zxx

for i in range(N):
  _, get_audio = wav.read(all_files[i])
  _, _, Zxx1 = stft(yf1, fs, nperseg=1000, noverlap=500)
  all_data1[0:Zxx1.shape[0],0:Zxx1.shape[1],i]=Zxx1

for i in range(N):
  _, get_audio = wav.read(all_files[i])
  _, _, Zxx2 = stft(yf2, fs, nperseg=1000, noverlap=500)
  all_data2[0:Zxx2.shape[0],0:Zxx2.shape[1],i]=Zxx2

print(all_data.shape)
#plot just for testing
print(get_audio.shape)
plt.xlabel('time')
plt.plot(get_audio)
plt.grid()
plt.show()

"""CNN
  
IMPORTANT!!!!!!!!: You must go to the tool bar at the top and select runtime>change runtime type>GPU (not CPU).  This code will take several minutes on GPU and several hours on CPU 

To do: implement 1 model per filterbank as shown
"""

from keras.models import Sequential
from keras.layers import Dense, Activation

from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, UpSampling2D
from keras.optimizers import Adam
import numpy as np


#BAND 1
#3 models per the 3 freq bands, each of the 3 take in corresponding
# stft from above (i.e. all_data, all_data1, all_data2)

input1 = np.transpose(all_data, (2, 0, 1)) #change dimensions to match required form for input
n_frame=input1.shape[1]
frame_size=input1.shape[2]
input1 = input1[..., None] # keras needs 4D input, so add 1 dimension
phase=np.angle(input1) #get phase as output
magnitude=np.abs(input1) #get magnitude for input

# you can change any parameters that you want here, but runtime goes up exponentially with increasing number of layers or parameters
model = Sequential() #begin a sequential model
print(n_frame)
model.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model.compile(loss='mean_squared_error', optimizer=adam)

model.fit(magnitude, phase, batch_size=100, epochs=5) #can increase epoch# if loss is still decreasing after last epoch


model = Sequential() #begin a sequential model
print(n_frame)
model.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model.compile(loss='mean_squared_error', optimizer=adam)

model.fit(magnitude, phase, batch_size=100, epochs=5)

model = Sequential() #begin a sequential model
print(n_frame)
model.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model.compile(loss='mean_squared_error', optimizer=adam)

model.fit(magnitude, phase, batch_size=100, epochs=5)

#BAND 2

input2 = np.transpose(all_data1, (2, 0, 1)) #change dimensions to match required form for input
n_frame=input2.shape[1]
frame_size=input2.shape[2]
input2 = input2[..., None] # keras needs 4D input, so add 1 dimension
phase2=np.angle(input2) #get phase as output
magnitude2=np.abs(input2) #get magnitude for input

# you can change any parameters that you want here, but runtime goes up exponentially with increasing number of layers or parameters
model2 = Sequential() #begin a sequential model
print(n_frame)
model2.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model2.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model2.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model2.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam2 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model2.compile(loss='mean_squared_error', optimizer=adam2)

model2.fit(magnitude2, phase2, batch_size=100, epochs=5) #can increase epoch# if loss is still decreasing after last epoch

model2 = Sequential() #begin a sequential model
print(n_frame)
model2.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model2.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model2.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model2.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam2 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model2.compile(loss='mean_squared_error', optimizer=adam2)

model2.fit(magnitude2, phase2, batch_size=100, epochs=5)

model2 = Sequential() #begin a sequential model
print(n_frame)
model2.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model2.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model2.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model2.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model2.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam2 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model2.compile(loss='mean_squared_error', optimizer=adam2)

model2.fit(magnitude2, phase2, batch_size=100, epochs=5)

#BAND 3

input3 = np.transpose(all_data2, (2, 0, 1)) #change dimensions to match required form for input
n_frame=input3.shape[1]
frame_size=input3.shape[2]
input3 = input3[..., None] # keras needs 4D input, so add 1 dimension
phase3=np.angle(input3) #get phase as output
magnitude3=np.abs(input3) #get magnitude for input

# you can change any parameters that you want here, but runtime goes up exponentially with increasing number of layers or parameters
model3 = Sequential() #begin a sequential model
print(n_frame)
model3.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model3.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model3.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model3.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam3 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model3.compile(loss='mean_squared_error', optimizer=adam3)

model3.fit(magnitude3, phase3, batch_size=100, epochs=5) #can increase epoch# if loss is still decreasing after last epoch

model3 = Sequential() #begin a sequential model
print(n_frame)
model3.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model3.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model3.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model3.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam3 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model3.compile(loss='mean_squared_error', optimizer=adam3)

model3.fit(magnitude3, phase3, batch_size=100, epochs=5)

model3 = Sequential() #begin a sequential model
print(n_frame)
model3.add(Conv2D(16, (9,9), input_shape=(n_frame, frame_size, 1), activation='relu', padding='same')) #choose h1 is a 9 x 9 x 16 convolution kernel
model3.add(MaxPooling2D(pool_size=(2, 2))) #down sample by 2x2 for nonlinearity
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h2 is a 5 x 5 x 32 convolution kernel
#model.add(Dropout(0.5))
model3.add(Conv2D(32, (5, 5), activation='relu', padding='same')) #choose h3 is a 5 x 5 x 32 convolution kernel
model3.add(UpSampling2D((2, 2))) #upsample by 2 x 2 for nonlinearity
model3.add(Conv2D(1, (9, 9), activation='relu', padding='same')) #choose h4 is a 9 x 9 x 1 convolution kernel

adam3 = Adam(learning_rate=0.0001, decay=1e-2, beta_1=0.9, beta_2=0.999, amsgrad=False)
#can decrease learning rate or decay for more training, takes longer, tho
model3.compile(loss='mean_squared_error', optimizer=adam3)

model3.fit(magnitude3, phase3, batch_size=100, epochs=5)

"""Guess phase from model and reconstruct
To do: Reconstruct from filterbanks
"""

from scipy.signal import istft

#model 1
guess_phase = model.predict(magnitude)
reconst = magnitude *np.exp(1j*guess_phase)
_, reconstructed_signal1=istft(reconst[0,:,:,0],fs)

#model 2
guess_phase2 = model2.predict(magnitude2)
reconst2 = magnitude2 *np.exp(1j*guess_phase)
_, reconstructed_signal2=istft(reconst2[0,:,:,0],fs)

 #model 3
guess_phase3 = model3.predict(magnitude3)
reconst3 = magnitude3 *np.exp(1j*guess_phase)
_, reconstructed_signal3=istft(reconst3[0,:,:,0],fs)

#sum the reconstructed bands
total_reconstruct = reconstructed_signal1 + reconstructed_signal2 + reconstructed_signal3
print(total_reconstruct)

#outputs the home drive
wav.write('/content/gdrive/My Drive/000reconstruct.wav',fs,np.real(total_reconstruct).astype('int16'))

"""Turn in: 
1. Your code
2. 000reconstruct.wav
3. An explanation of your design choices and analysis of your results
"""