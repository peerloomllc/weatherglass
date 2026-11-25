# "Noir" skin: a 1940s detective film. Stark white shapes on black, cut
# across by the striped shadow of venetian blinds, with hard rain.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_noir.py -- art/noir.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials


def blinds(lit, shade, period=0.11, duty=0.62, angle=math.radians(-28)):
    """Color in diagonal stripes: "lit" where light comes through the
    blinds, "shade" in the slats' shadow. Stripes line up across shapes."""
    name = f"blinds_{lit}_{shade}"
    if name in kit._mats:
        return kit._mats[name]
    m, nt, out = kit._new(name)
    m.diffuse_color = kit.srgb(lit)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    # d = (x sin a + y cos a) / period, stripe = fract(d) < duty
    xs = nt.nodes.new("ShaderNodeMath")
    xs.operation = "MULTIPLY"
    xs.inputs[1].default_value = math.sin(angle) / period
    ys = nt.nodes.new("ShaderNodeMath")
    ys.operation = "MULTIPLY_ADD"
    ys.inputs[1].default_value = math.cos(angle) / period
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = duty
    nt.links.new(sep.outputs["X"], xs.inputs[0])
    nt.links.new(sep.outputs["Y"], ys.inputs[0])
    nt.links.new(xs.outputs[0], ys.inputs[2])
    nt.links.new(ys.outputs[0], fr.inputs[0])
    nt.links.new(fr.outputs[0], lt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = kit.srgb(shade)
    mix.inputs["B"].default_value = kit.srgb(lit)
    nt.links.new(lt.outputs[0], mix.inputs["Factor"])
    return kit._finish(m, nt, out, mix.outputs["Result"], 1.0)


WHITE = blinds("#F2F2F2", "#7A7A7A")


class Noir(kit.Style):
    def sun(self, c, x, y, s, z):
        for i in range(8):
            a = 2 * math.pi * i / 8 + math.pi / 8
            kit.poly(c, WHITE, kit.capsule_pts(x + 0.64 * s * math.cos(a), y + 0.64 * s * math.sin(a), 0.2 * s, 0.05 * s, a),
                     z, "ray")
        kit.disc(c, WHITE, x, y, 0.45 * s, z, "sun")

    def moon(self, c, x, y, s, z):
        kit.poly(c, blinds("#E6E6E6", "#6E6E6E"), kit.crescent_pts(x, y, 0.55 * s), z, "moon")

    def star(self, c, x, y, r, z):
        kit.poly(c, kit.flat("#F2F2F2"), kit.star_pts(x, y, r * 1.2, 4, 0.22), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        m = blinds("#6A6A6A", "#3A3A3A") if dark else blinds("#CFCFCF", "#6E6E6E")
        kit.poly(c, m, kit.cloud_outline(x, y, s), z, "cloud")

    def raindrop(self, c, x, y, z):
        for dx, dy, ln in ((0, 0, 0.4), (0.1, 0.15, 0.28)):
            kit.poly(c, kit.flat("#F2F2F2", 0.9), kit.capsule_pts(x + dx, y + dy, ln, 0.022, math.radians(80)), z, "rain")

    def drizzle(self, c, x, y, z):
        kit.poly(c, kit.flat("#F2F2F2", 0.85), kit.capsule_pts(x, y, 0.12, 0.02, math.radians(80)), z, "rain")

    def flake(self, c, x, y, r, z):
        kit.disc(c, kit.flat("#F2F2F2"), x, y, r * 0.42, z, "snow")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, kit.flat("#BDBDBD", 0.55, alpha_grain=0.3, grain_scale=10, stretch=8),
                     kit.capsule_pts(x, y, w, 0.2), z, "smoke")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, kit.flat("#F2F2F2"), kit.bolt_pts(x, y, s, 1.15), z, "bolt")


kit.build(Noir())
kit.save()
