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

from appimagebuilder.common.finder import Finder
from appimagebuilder.main.commands.apt_deploy_command import AptDeployCommand
from appimagebuilder.main.commands.create_appimage_command import CreateAppImageCommand
from appimagebuilder.main.commands.file_deploy_command import FileDeployCommand
from appimagebuilder.main.commands.pacman_deploy_command import PacmanDeployCommand
from appimagebuilder.main.commands.run_shell_script_command import RunShellScriptCommand
from appimagebuilder.main.commands.run_test_command import RunTestCommand
from appimagebuilder.main.commands.setup_symlinks_command import SetupSymlinksCommand
from appimagebuilder.recipe.roamer import Roamer


class Orchestrator:
    """Transforms a recipe into a command list"""

    def __init__(self):
        self._cache_dir_name = "appimage-builder-cache"

    def prepare_commands(self, recipe: Roamer, args):
        if recipe.version() == 1:
            return self._prepare_commands_for_recipe_v1(args, recipe)

        return []

    def _prepare_commands_for_recipe_v1(self, args, recipe):
        commands = []
        if not args.skip_script:
            command = RunShellScriptCommand(
                "main script", recipe.AppDir.path(), recipe.script
            )
            commands.append(command)

        if not args.skip_build:
            commands.extend(self._create_app_dir_commands(recipe))

        if not args.skip_tests and recipe.AppDir.test:
            command = RunTestCommand(recipe.AppDir.path(), recipe.AppDir.test)
            commands.append(command)

        if not args.skip_appimage:
            command = CreateAppImageCommand(recipe)
            commands.append(command)

        return commands

    def _create_app_dir_commands(self, recipe):
        commands = []
        app_dir_path = recipe.AppDir.path()
        cache_dir_path = os.path.join(os.getcwd(), self._cache_dir_name)

        self._create_deploy_commands(app_dir_path, cache_dir_path, commands, recipe)

        self._create_setup_commands(app_dir_path, commands)

        return commands

    def _create_deploy_commands(self, app_dir_path, cache_dir_path, commands, recipe):
        # bundle section
        if recipe.AppDir.before_bundle:
            command = RunShellScriptCommand(
                "before bundle script", app_dir_path, recipe.AppDir.before_bundle
            )
            commands.append(command)
        apt_section = recipe.AppDir.apt
        if apt_section:
            command = self._generate_apt_deploy_command(
                app_dir_path, apt_section, cache_dir_path, {}
            )
            commands.append(command)
        pacman_section = recipe.AppDir.pacman
        if pacman_section:
            command = self._generate_pacman_deploy_command(
                app_dir_path, pacman_section, cache_dir_path, {}
            )
            commands.append(command)
        files_section = recipe.AppDir.files
        if files_section:
            command = FileDeployCommand(
                app_dir_path,
                cache_dir_path,
                {},
                files_section.include() or [],
                files_section.exclude() or [],
            )
            commands.append(command)
        if recipe.AppDir.after_bundle:
            command = RunShellScriptCommand(
                "after bundle script", app_dir_path, recipe.AppDir.after_bundle
            )
            commands.append(command)

    def _create_setup_commands(self, app_dir_path, commands):
        # runtime section
        finder = Finder(app_dir_path)
        commands.append(
            SetupSymlinksCommand(
                app_dir_path,
                finder
            )
        )

    def _generate_apt_deploy_command(
        self, app_dir_path, apt_section, cache_dir_path, deploy_record
    ):
        apt_archs = apt_section.arch()
        if isinstance(apt_archs, str):
            apt_archs = [apt_archs]

        sources = []
        keys = []
        for item in apt_section.sources():
            if "sourceline" in item:
                sources.append(item["sourceline"])
            if "key_url" in item:
                keys.append(item["key_url"])

        return AptDeployCommand(
            app_dir_path,
            cache_dir_path,
            deploy_record,
            apt_section.include(),
            apt_section.exclude() or [],
            apt_archs,
            sources,
            keys,
            apt_section.allow_unauthenticated() or False,
        )

    def _generate_pacman_deploy_command(
        self, app_dir_path, pacman_section, cache_dir_path, deploy_record
    ):
        return PacmanDeployCommand(
            app_dir_path,
            cache_dir_path,
            deploy_record,
            pacman_section.include(),
            pacman_section.exclude(),
            pacman_section["Architecture"](),
            pacman_section.repositories(),
            pacman_section.options(),
        )