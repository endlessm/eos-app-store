import alsaaudio

mix = alsaaudio.Mixer()
#Always need to make a new Mixer object to reflect new volume level
print mix.getvolume()
