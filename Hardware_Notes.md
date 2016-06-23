Hardware Notes
==============

Set_Clock.ino will set the DS1077 programmable oscilator
to a set kHz frequency. The Due does not seem to be able
to handle interrupts at a frequency too much greater than 
about 100 kHz, despite the 80 MHz clock frequency on the
Sam3x processor.

Spec_Duino_Fake.ino will communicate with the UI as if
collecting spectra, but it will really just generate data
with a random algorithm. It is useful for sorting out 
connectivity issues without the complications of gathering
real data. Note that there are currently communications
problems. The 'SPEC' message which is meant to identify a
successful connection seems to get garbled. I think a more
robust handshake could fix this, but right now I just allow
any connection instead.

ILX511B_Due_Driver.ino is very incomplete, but will be the
final firmware for the Due. What is missing is a robust
way to send a start signal to the ILX511B in sync with the
proper clock phase. The START pin (currently 2) is meant
For this, and two interrupts track the phase of the clock.
Here is a bit of background on this decision. The start
signal must rise and fall on certain phases of the clock
(see the datasheet). It would be simple to have the DUE
control both the clock and the start signal. It would 
always know the clock phase, etc. The problem is, that 
during serial communication the normal interrupts are 
suspended so the clock would fibrillate and fail after 
each acquisition as the data was sent to the UI. Even
though we are not collecting data during this time,
disrupting the clock at any time will jeopardize the data
taken once the clock is re-established. That is why I 
chose to do an asynchronous clock with the DS1077. Now,
however, we need to ensure that the integration signal is
phase-locked with the asynchronous clock. For the InGaAs
array, I used a flip-flop to synchronize them in hardware,
which could still be an option here. Instead, though, I 
was trying to get it all synced up in software with 
interrupts tracking both the rising and falling edges of
the clock.

Good luck!
