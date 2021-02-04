#  Copyright  2021 Alexis Lopez Zubieta
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
import os
import pathlib

from appimagebuilder.builder import steps
from appimagebuilder.builder.step import Step


class PlannerV1:
    """Generates a set of runnable steps from a type 1 recipe  to achieve the ultimate goal of producing an AppImage"""

    def __init__(self, recipe):
        self.recipe = recipe

        self.skip_script = False
        self.skip_build = False
        self.skip_tests = False
        self.skip_appimage = False

        recipe_version = self.recipe.get_item("version")
        if recipe_version != 1:
            raise RuntimeError("Unknown recipe version: '%s'" % recipe_version)

        self.build_dir = pathlib.Path(os.getcwd()).absolute() / "build"
        self.appdir = self.recipe.get_item("AppDir/path", self.build_dir / "AppDir")
        self.appdir = pathlib.Path(self.appdir).absolute()

        self._steps = []

    def plan(self) -> [Step]:
        self._steps.clear()

        if not self.skip_script:
            self._generate_main_script_step()

        if not self.skip_build:
            self._generate_before_bundle_step()
            self._generate_apt_step()
            self._generate_after_bundle_step()

        return self._steps

    def _get_build_env(self):
        build_env = os.environ.copy()
        build_env["BUILD_DIR"] = self.build_dir.__str__()
        build_env["APPDIR"] = self.appdir.__str__()
        return build_env

    def _generate_main_script_step(self):
        script = self.recipe.get_item("script", "")
        if script:
            step = steps.Script("script", script, self._get_build_env())
            self._steps.append(step)

    def _generate_before_bundle_step(self):
        script = self.recipe.get_item("AppDir/before_bundle", "")
        if script:
            step = steps.Script("before_bundle script", script, self._get_build_env())
            self._steps.append(step)

    def _generate_after_bundle_step(self):
        script = self.recipe.get_item("AppDir/after_bundle", "")
        if script:
            step = steps.Script("after_bundle script", script, self._get_build_env())
            self._steps.append(step)

    def _generate_apt_step(self):
        pass
