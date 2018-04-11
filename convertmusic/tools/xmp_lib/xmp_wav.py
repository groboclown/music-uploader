
from .libxmp import (
    ModuleInfo, FrameInfo,

    xmp_set_player, xmp_create_context, xmp_set_player,
    xmp_load_module, xmp_start_player, xmp_get_player,
    xmp_play_frame, xmp_get_frame_info, xmp_end_player, xmp_release_module,
    xmp_free_context, xmp_get_module_info, xmp_set_position,

    XMP_INTERP_SPLINE, XMP_DSP_LOWPASS, XMP_DSP_ALL, XMP_MODE_AUTO,
    XMP_FLAGS_VBLANK, XMP_FLAGS_FX9BUG, XMP_FLAGS_FIXLOOP, XMP_FLAGS_A500,

    XMP_PLAYER_DEFPAN, XMP_PLAYER_VOICES, XMP_PLAYER_INTERP, XMP_PLAYER_DSP,
    XMP_PLAYER_AMP, XMP_PLAYER_CFLAGS,
)
import wave
from ctypes import pointer

OPT_FREQUENCY = 44100
OPT_CHANNEL_COUNT = 2
OPT_BITS_PER_SAMPLE = 16
OPT_SAMPLE_WIDTH = OPT_BITS_PER_SAMPLE // 8
OPT_MIX = -1
OPT_DEFAULT_PAN = 50
OPT_NUMBER_VOICES = 128
OPT_INTERPOLATE = XMP_INTERP_SPLINE
OPT_DSP = XMP_DSP_ALL
OPT_PLAYER_MODE = XMP_MODE_AUTO
OPT_AMPLIFY = 1
OPT_VBLANK = 0 # Force vblank timing in Amiga modules
OPT_FX9BUG = 0 # offset bug emulation
OPT_FIXLOOP = 0 # Use sample loop start /2 in MOD/UNIC/NP3
OPT_AMIGA_MIXER = 0 # Use Paula simulation mixer in Amiga formats

# 16 bit, stereo, signed
OPT_FORMAT = 0


def _set_flag(flag, action, val):
    if action > 0:
        flag |= val
    elif action < 0:
        flag &= ~val
    return flag

def convert(inp_file, outp_file, loop_count = 0):
    assert isinstance(inp_file, str)

    xc = xmp_create_context()
    if xc == None:
        raise Exception()
    # must be set before loading module
    xmp_set_player(xc, XMP_PLAYER_DEFPAN, OPT_DEFAULT_PAN)
    rc = xmp_load_module(xc, bytes(inp_file, 'utf-8'))
    if rc < 0:
        raise Exception()
    module = ModuleInfo()
    xmp_get_module_info(xc, pointer(module))

    #print("Name: {0}".format(module.name))
    #print("Type: {0}".format(module.type))
    #print("Instruments: {0}   Samples: {0}".format(module.ins, module.smp))
    #for i in range(module.ins):
    #    ins = module.xxi[i]
    #    if len(ins.name.rstrip()) > 0:
    #        print(" {0} {1}".format(i, module.xxi[i].name))


    xmp_set_player(xc, XMP_PLAYER_VOICES, OPT_NUMBER_VOICES)
    rc = xmp_start_player(xc, OPT_FREQUENCY, OPT_FORMAT)
    if rc != 0:
        raise Exception()
    xmp_set_player(xc, XMP_PLAYER_INTERP, OPT_INTERPOLATE)
    xmp_set_player(xc, XMP_PLAYER_DSP, OPT_DSP)
    # if not auto mode,
    # xmp_set_player(xc, XMP_PLAYER_MODE, player mode)
    xmp_set_player(xc, XMP_PLAYER_AMP, OPT_AMPLIFY)
    # if mix >= 0:
    # xmp_set_player(xc, XMP_PLAYER_MIX, OPT_MIX)
    # if reversed, set mix to negative OPT_MIX
    xmp_set_position(xc, 0)

    # mute channels?!?
    flags = xmp_get_player(xc, XMP_PLAYER_CFLAGS)
    flags = _set_flag(flags, OPT_VBLANK, XMP_FLAGS_VBLANK)
    flags = _set_flag(flags, OPT_FX9BUG, XMP_FLAGS_FX9BUG)
    flags = _set_flag(flags, OPT_FIXLOOP, XMP_FLAGS_FIXLOOP)
    flags = _set_flag(flags, OPT_AMIGA_MIXER, XMP_FLAGS_A500)
    xmp_set_player(xc, XMP_PLAYER_CFLAGS, flags)

    out = wave.open(outp_file, 'wb')
    out.setnchannels(OPT_CHANNEL_COUNT)
    out.setsampwidth(OPT_SAMPLE_WIDTH)
    out.setframerate(OPT_FREQUENCY)

    fi = FrameInfo()
    fi.loop_count = 0
    while xmp_play_frame(xc) == 0:
        old_loop = fi.loop_count
        xmp_get_frame_info(xc, pointer(fi))
        if old_loop != fi.loop_count:
            # Looping!
            loop_count -= 1
            if loop_count <= 0:
                break
        b = fi.get_buffer()
        # print("Writing frme with {0} bytes".format(len(b)))
        out.writeframes(b)

    xmp_end_player(xc)
    xmp_release_module(xc)
    xmp_free_context(xc)
    out.close()


if __name__ == '__main__':
    import sys
    convert(sys.argv[1], sys.argv[2])
