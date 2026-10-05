"""Original soundtrack of the presentation videos (tools/make_video.py), synthesized with numpy: no sample, no
borrowed track. A calm steampunk adventure piece in D minor (i - VI - III - VII): warm pads, harp-like plucked
arpeggios, a bass, a ticking-clock percussion, low booms on the chapter cards, a bell for the title, and the UI
sounds (clicks, whooshes) in the same key and the same reverb, mixed under the music."""
import math
import wave

import numpy as np

SR = 44100
A4 = 440.0


def hz(midi):
    return A4 * 2 ** ((midi - 69) / 12)


# D minor: Dm, Bb, F, C (MIDI roots in octave 3) with their chord tones
CHORDS = [
    (50, [50, 53, 57]),  # Dm
    (46, [46, 50, 53]),  # Bb
    (53, [53, 57, 60]),  # F
    (48, [48, 52, 55]),  # C
]


def _env(n, attack, release, sr=SR):
    e = np.ones(n, np.float32)
    a = min(n, int(attack * sr))
    r = min(n - a, int(release * sr))
    if a > 0:
        e[:a] = np.linspace(0, 1, a) ** 1.5
    if r > 0:
        e[n - r:] *= np.linspace(1, 0, r) ** 1.2
    return e


def _add(buf, start, sig):
    i0 = int(start * SR)
    if i0 >= len(buf):
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), len(buf) - i0)
    buf[i0:i0 + n] += sig[:n]


def pad_note(freq, dur, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, np.float32)
    for det in (-0.004, 0.004):
        f = freq * (1 + det)
        for k in range(1, 7):
            amp = (1.0 / k) * (0.55 ** max(0, k - 2)) * (bright if k > 2 else 1.0)
            out += amp * np.sin(2 * np.pi * f * k * t + k * 0.7 + det * 400).astype(np.float32)
    # slow movement of the tone
    out *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * t + freq)).astype(np.float32)
    return out * _env(n, 1.1, 1.3)


def pluck(freq, dur=1.6, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 9):
        f = freq * k * (1 + 0.0007 * k * k)
        amp = (1.0 / k ** 1.25) * (bright ** (k - 1))
        out += amp * np.exp(-t * (2.2 + 1.1 * k)) * np.sin(2 * np.pi * f * t)
    attack = min(n, int(0.004 * SR))
    out[:attack] *= np.linspace(0, 1, attack)
    return out


def bass_note(freq, dur):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.sin(2 * np.pi * freq * t) + 0.28 * np.sin(4 * np.pi * freq * t) + 0.08 * np.sin(6 * np.pi * freq * t)
    return (out * np.exp(-t * 1.1) * _env(n, 0.02, 0.25)).astype(np.float32)


def tick(high=True):
    n = int(0.05 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 2600 if high else 1900
    rng = np.random.default_rng(7 if high else 11)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + 0.35 * rng.standard_normal(n) * np.exp(-t * 400)
    return s.astype(np.float32)


def boom(depth=1.0, dur=2.2):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 38 + 34 * np.exp(-t * 7)
    phase = 2 * np.pi * np.cumsum(f) / SR
    rng = np.random.default_rng(3)
    s = np.sin(phase) * np.exp(-t * 1.8) + 0.05 * rng.standard_normal(n) * np.exp(-t * 40)
    return (s * depth).astype(np.float32)


def kick():
    n = int(0.4 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 50 + 70 * np.exp(-t * 25)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)


def bell(freq, dur=3.5):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, np.float32)
    for ratio, amp, decay in ((1.0, 1.0, 1.2), (2.0, 0.5, 1.8), (2.76, 0.35, 2.4), (5.4, 0.18, 4.0), (8.93, 0.08, 6.0)):
        out += amp * np.exp(-t * decay) * np.sin(2 * np.pi * freq * ratio * t)
    out[:int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return out


def ui_click():
    n = int(0.09 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    s = 0.7 * np.sin(2 * np.pi * hz(81) * t) * np.exp(-t * 60) + 0.5 * np.sin(2 * np.pi * hz(74) * t) * np.exp(-t * 45)
    s += tick(True)[:n] * 0.5 if n <= len(tick(True)) else 0
    return s.astype(np.float32)


def whoosh(dur=0.55, up=True):
    """Air moving past: band-limited noise whose band slides up (or down), swelling and fading."""
    n = int(dur * SR)
    rng = np.random.default_rng(5 if up else 9)
    noise = rng.standard_normal(n).astype(np.float32)
    lo = lowpass(noise, 900)
    hi = lowpass(noise, 4200) - lo
    u = np.linspace(0, 1, n, dtype=np.float32)
    mix = u if up else 1 - u
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return ((lo * (1 - mix) + hi * mix) * env * 1.6).astype(np.float32)


def riser(dur=2.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n, dtype=np.float32)
    rng = np.random.default_rng(13)
    noise = rng.standard_normal(n).astype(np.float32)
    # brighter as it rises: mix of smoothed and raw noise
    smooth = np.convolve(noise, np.ones(24) / 24, mode="same")
    s = (smooth * (1 - t) + noise * t * 0.35) * t ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(220 + 440 * t ** 2) / SR) * t ** 3 * 0.25
    return (s + tone).astype(np.float32)


def reverb(x, seconds=1.8, seed=1):
    """Convolution with a decaying noise tail (FFT): one shared room for the music and the effects."""
    n = int(seconds * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2 / seconds * 2.2)
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(math.ceil(math.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y.astype(np.float32)


def lowpass(x, cutoff, order=2):
    """Zero-phase low-pass in the frequency domain (a Butterworth magnitude)."""
    size = 1 << int(math.ceil(math.log2(len(x) + 1)))
    spec = np.fft.rfft(x, size)
    f = np.fft.rfftfreq(size, 1 / SR)
    spec *= 1 / np.sqrt(1 + (f / cutoff) ** (2 * order))
    return np.fft.irfft(spec, size)[: len(x)].astype(np.float32)


def smooth_curve(points, total, ramp=0.6):
    """Piecewise level curve [(t0, t1, level)] with soft ramps, sampled at SR."""
    n = int(total * SR)
    curve = np.zeros(n, np.float32)
    for t0, t1, lvl in points:
        curve[int(t0 * SR):int(t1 * SR)] = lvl
    k = max(1, int(ramp * SR))
    kernel = np.ones(k, np.float32) / k
    return np.convolve(curve, kernel, mode="same").astype(np.float32)


def compose(total, bpm, sections, hits=(), clicks=(), whooshes=(), bells=(), risers=(), seed=0, energy=1.0):
    """The whole soundtrack as a stereo float array.

    sections: [(t0, t1, level)] with level 0 (pad), 1 (+ arpeggio, bass), 2 (+ ticks and soft kick).
    hits: boom times; clicks: UI click times; whooshes: transition times; bells: (time, midi) chimes."""
    n = int(total * SR) + SR
    beat = 60.0 / bpm
    bar = beat * 4
    pad = np.zeros(n, np.float32)
    arp_l = np.zeros(n, np.float32)
    arp_r = np.zeros(n, np.float32)
    bass = np.zeros(n, np.float32)
    perc = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)

    patterns = [[0, 1, 2, 3, 4, 3, 2, 1], [0, 2, 1, 3, 2, 4, 3, 5], [0, 1, 2, 4, 3, 2, 1, 2], [4, 3, 2, 1, 2, 3, 4, 5]]
    chord_len = bar * 2
    i = 0
    t = 0.0
    while t < total + chord_len:
        root, tones = CHORDS[i % len(CHORDS)]
        for m in tones:
            _add(pad, t - 0.3, pad_note(hz(m), chord_len + 1.2, bright=0.8) * 0.33)
            _add(pad, t - 0.3, pad_note(hz(m + 12), chord_len + 1.2, bright=0.5) * 0.12)
        # bass on beats 1 and 3, a passing note at the end of the second bar
        for b, m in ((0, root - 12), (2, root - 12), (4, root - 12), (6, root - 12), (7, root - 12 + (7 if i % 2 else 5))):
            _add(bass, t + b * beat, bass_note(hz(m), beat * (2 if b < 7 else 1) + 0.2))
        # arpeggio in eighths over two octaves of the chord
        notes = sorted(tones) + [m + 12 for m in sorted(tones)]
        pat = patterns[(i // 4) % len(patterns)]
        for s in range(16):
            m = notes[pat[s % 8] % len(notes)] + 12
            vel = (0.8 if s % 4 == 0 else 0.55) * (0.9 + 0.2 * rng.random())
            p = pluck(hz(m), 1.5, bright=0.8) * vel
            _add(arp_l, t + s * beat / 2, p * (0.75 if s % 2 == 0 else 0.4))
            _add(arp_r, t + s * beat / 2, p * (0.4 if s % 2 == 0 else 0.75))
        # ticking clock in eighths, tock on the off-beats, a soft kick on beats 1 and 3
        for s in range(16):
            _add(perc, t + s * beat / 2, tick(s % 2 == 0) * (0.5 if s % 2 == 0 else 0.32))
        for b in (0, 2, 4, 6):
            _add(perc, t + b * beat, kick() * 0.55)
        t += chord_len
        i += 1

    lvl_arp = smooth_curve([(a, b, 1.0 if l >= 1 else 0.0) for a, b, l in sections], total + 1)
    lvl_perc = smooth_curve([(a, b, 1.0 if l >= 2 else 0.0) for a, b, l in sections], total + 1)
    lvl_bass = smooth_curve([(a, b, 1.0 if l >= 1 else 0.35) for a, b, l in sections], total + 1)
    m = min(n, len(lvl_arp))
    for buf in (arp_l, arp_r):
        buf[:m] *= lvl_arp[:m]
        buf[m:] = 0
    perc[:m] *= lvl_perc[:m]
    perc[m:] = 0
    bass[:m] *= lvl_bass[:m]
    bass[m:] = 0

    for h in hits:
        _add(fx, h, boom(1.0))
    for c in clicks:
        _add(fx, c, ui_click() * 0.32)
    for w_ in whooshes:
        _add(fx, w_ - 0.25, whoosh(0.55) * 0.14)
    for tb, midi in bells:
        _add(fx, tb, bell(hz(midi)) * 0.35)
    for tr, dur in risers:
        _add(fx, tr - dur, riser(dur) * 0.5)

    bass = lowpass(bass, 420)
    pad = lowpass(pad, 1600)
    # nothing harsh: the clicks and noises keep below the air band
    perc = lowpass(perc, 5200)
    fx = lowpass(fx, 6500)
    left = 0.55 * pad + 0.9 * arp_l + 0.75 * bass + 0.42 * perc * energy + 0.8 * fx
    right = 0.55 * pad + 0.9 * arp_r + 0.75 * bass + 0.42 * perc * energy + 0.8 * fx
    wet_l = reverb(0.6 * pad + arp_l + 0.5 * fx, 2.2, seed=1)
    wet_r = reverb(0.6 * pad + arp_r + 0.5 * fx, 2.2, seed=2)
    left = left + 0.32 * wet_l
    right = right + 0.32 * wet_r
    out = np.stack([left, right], axis=1)[: int(total * SR)]
    # fades, then a gentle limiter
    fade_in = min(len(out), int(1.2 * SR))
    out[:fade_in] *= np.linspace(0, 1, fade_in)[:, None] ** 1.5
    fade_out = min(len(out), int(2.5 * SR))
    out[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None] ** 1.3
    peak = np.abs(out).max() or 1.0
    out = out / peak * 0.9
    out = np.tanh(out * 1.3) / np.tanh(1.3)
    return out.astype(np.float32)


def write_wav(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32000).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
