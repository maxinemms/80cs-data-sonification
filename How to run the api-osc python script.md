How to receive in Sonic Pi

To get python script working: (written in Python 3.9.1)

install osc client 

use pip install python-osc

to run the script:
look at the IP address from 'IO' - 'Local IP Addresses'

then run 
python osc_client.py --ip 192.168.0.5

in Sonic Pi code use "sync" like these:
Example:
live_loop :foo do
  use_real_time
  a = sync "/osc*/trigger/soundpressure"
  b = sync "/osc*/trigger/airquality"
  c = sync "/osc*/trigger/temperature"
  d = sync "/osc*/trigger/humidity"
  e = sync "/osc*/trigger/airpressure"
  synth :prophet, note: a, cutoff: b, sustain: c
end