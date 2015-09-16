import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import sublime
import sublime_plugin
import itertools
import json

from .lib.io import load_python_file, write_sublimious_file
from .lib.collector import Collector


def plugin_loaded():
    current_path = os.path.dirname(os.path.realpath(__file__))

    sublime_dir = os.path.dirname(sublime.packages_path())
    packages_dir = os.path.join(sublime_dir, 'Packages')
    user_dir = os.path.join(packages_dir, 'User')

    status_panel = sublime.active_window().create_output_panel("sublimious_status_panel")
    sublime.active_window().run_command("show_panel", {"panel": "output.sublimious_status_panel", "toggle": False})
    status_panel.run_command("status", {"text": "Welcome to Sublimious."})

    pcontrol_settings = os.path.join(user_dir, 'Package Control.sublime-settings')
    settings_file = os.path.join(user_dir, 'Preferences.sublime-settings')

    collector = Collector(current_path)

    # Second iteration to initialise all layers with config
    collected_config = collector.get_collected_config()
    for layer in collector.get_layers():
        layer.init(collected_config)
        status_panel.run_command("status", {"text": "'%s' layer loaded..." % layer.name})

    # Collect all packages
    status_panel.run_command("status", {"text": "Collecting all packages..."})
    all_packages = collector.collect_key("required_packages") + collector.get_user_config().additional_packages
    write_sublimious_file(pcontrol_settings, json.dumps({'installed_packages': all_packages}))

    # Get all keybinding definitions and save to keymapfile
    status_panel.run_command("status", {"text": "Building keymap..."})
    write_sublimious_file("%s/Default.sublime-keymap" % current_path, json.dumps(collector.collect_key("sublime_keymap")))

    # Generate a bunch of syntax files depending on layer config
    syntax_definitions = collector.collect_syntax_specific_settings()
    for syntax, value in syntax_definitions.items():
        write_sublimious_file("%s/%s.sublime-settings" % (current_path, syntax), json.dumps(value))
        status_panel.run_command("status", {"text": "Collected %s syntax definition..." % syntax})

    # Take control over sublime settings file
    status_panel.run_command("status", {"text": "Taking control over Preferences.sublime-settings..."})
    write_sublimious_file(settings_file, json.dumps(collected_config))

    status_panel.run_command("status", {"text": "ALL DONE!"})
    status_panel.run_command("status", {"text": "(this window will self close in 5s)"})


    sublime.set_timeout(lambda: sublime.active_window().run_command("hide_panel", {"panel": "output.sublimious_status_panel", "toggle": False}), 5000)
