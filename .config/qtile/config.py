#!/usr/bin/env python3

from subprocess import Popen, PIPE, run
import os

from libqtile import bar, layout, widget, hook, qtile
from libqtile.config import Click, Drag, Group, Key, KeyChord, Match, Screen
from libqtile.lazy import lazy
from libqtile.log_utils import logger

mod = "mod4"
terminal = "kitty"
home = "/home/amroj"

orange = "#ffa500"
black = "#000000"


@hook.subscribe.startup_once
def autostart():
    run([os.path.expanduser("~/.config/qtile/autostart.sh")])


def dmenu_groups(groups):
    return set(map(lambda x: x.name, groups))


def choose_group():
    @lazy.function
    def func(qtile):
        folders = os.listdir(f"{home}/dev")
        choices = dmenu_groups(qtile.groups)
        choices.update(folders)
        out = ""
        with Popen(["rofi", "-dmenu"], stdout=PIPE, stderr=PIPE, stdin=PIPE, text=True) as p:
            out = p.communicate(input="\n".join(choices))[0]
            out = out.rstrip("\n")

        if out in qtile.groups_map:
            qtile.groups_map[out].toscreen()
        elif out in folders:
            qtile.addgroup(out)
            qtile.groups_map[out].toscreen()
            path = f"{home}/dev/{out}"
            qtile.spawn(f"{terminal} -e hx {path}")
            qtile.spawn(f"{terminal} {path}")
            qtile.spawn(f"{terminal} {path}")
        elif out:
            qtile.addgroup(out)
            qtile.groups_map[out].toscreen()
    return func


def baseGroup(name: str, spawn: str):
    @lazy.function
    def func(qtile):
        qtile.groups_map[name].toscreen()
        g = qtile.current_group
        if len(g.windows) == 0:
            qtile.spawn(spawn)
    return func


lastGroup = ("", "")


@hook.subscribe.setgroup
def setgroup():
    global lastGroup
    lastGroup = (lastGroup[1], qtile.current_group.name)
    logger.warning(lastGroup)


def goto_last_group():
    @lazy.function
    def func(qtile):
        group = lastGroup[0]
        if group in qtile.groups_map:
            qtile.groups_map[group].toscreen()
    return func


def move_window():
    @lazy.function
    def func(qtile):
        choices = dmenu_groups(qtile.groups)
        with Popen(["rofi", "-dmenu"], stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True) as p:
            out = p.communicate(input="\n".join(choices))[0].rstrip("\n")
            if out in qtile.groups_map:
                qtile.current_window.togroup(out)
            elif out:
                qtile.addgroup(out)
                qtile.current_window.togroup(out)
    return func


keys = [
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod, "shift"], "k", lazy.layout.grow()),
    Key([mod, "shift"], "j", lazy.layout.shrink()),
    Key([mod, "shift"], "n", lazy.layout.normalize(),
        desc="Reset all window sizes"),
    Key([mod], "f", lazy.layout.swap_main(),
        desc="Swap current window with main"),
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),

    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "t", lazy.window.toggle_floating(),
        desc="Toggle floating on the focused window"),
    Key([mod], "m", lazy.window.toggle_minimize(), desc="Toggle maximize"),
    Key([mod, "shift"], "m", lazy.group.unminimize_all(),
        desc="Unminimize all"),

    Key([], "Print", lazy.spawn("flameshot full"),
        desc="Screenshot the screen"),
    Key(["shift"], "Print", lazy.spawn("flameshot gui"),
        desc="Screenshot the selected area"),

    Key([mod], "n", lazy.spawn(["rofi", "-show", "drun"]),
        desc="Spawn a command using a prompt widget"),
    Key([mod], "b", lazy.spawn("firefox"), desc="Launch firefox"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),

    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),

    Key([mod], "g", choose_group(), desc="Put to screen a group"),
    Key([mod, "shift"], "g", move_window(), desc="Move window"),
    Key([mod], "a", goto_last_group(), desc="Put to screen last visited group"),
    Key([mod], "z", baseGroup("browsing", "firefox")),
    Key([mod], "x", baseGroup("notes", "obsidian")),
    Key([mod], "c", baseGroup("pdf", "okular")),
    Key([mod], "v", baseGroup("thunderbird", "thunderbird")),
]

groups = [Group("browsing", label="\U0001F310",
                matches=[Match(wm_class="firefox")]),
          Group("notes", label="🗒", matches=[Match(wm_class="obsidian")]),
          Group("pdf", label="\U0001F5B9", matches=[Match(title="Okular")]),
          Group("thunderbird", label="\U0001F582",
                matches=[Match(wm_class="Mail")])]

layouts = [
    layout.MonadTall(ratio=0.5,
                     margin=8,
                     new_client_position="bottom",
                     border_width=5,
                     align=layout.MonadTall._left),
    layout.Max(),
]

widget_defaults = dict(
    font="sans",
    fontsize=12,
    padding=3,
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        wallpaper="~/Pictures/heic2007a.jpg",
        top=bar.Bar(
            [
                widget.GroupBox(),
                widget.WindowName(),
                widget.TextBox("Press &lt;M-n&gt; to spawn",
                               foreground="#d75f5f"),
                widget.Systray(),
                widget.Clock(format="%Y-%m-%d %a %I:%M %p", foreground=black,
                             background=orange, padding=10),
                widget.QuickExit(),
            ],
            24,
            border_width=[0, 0, 2, 0],  # Draw top and bottom borders
            border_color=[black, black, orange, black]
        ))
    ]

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

follow_mouse_focus = False
bring_front_click = "floating_only"
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

auto_minimize = True
wmname = "LG3D"
