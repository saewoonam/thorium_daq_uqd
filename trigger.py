from ruamel.yaml import YAML
import shm_buffer

yaml = YAML()
cmd = shm_buffer.CmdBuffer()

def set_trigger(ch, level):
    f = shm_buffer.shm.read_file('settings.yaml')
    new_settings = yaml.load(f)
    f.close()
    new_settings[ch][0] = level
    f = shm_buffer.shm.write_file('settings.yaml')
    yaml.dump(new_settings, f)
    f.close()
    cmd.write('trigger')
