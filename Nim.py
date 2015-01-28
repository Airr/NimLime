import sublime
import sublime_plugin
import re
import subprocess
import os

try:  # Python 3
    from NimLime.Project import Utility
except ImportError:  # Python 2:
    from Project import Utility


class Idetools:

    service = None

    # Fields
    pattern = re.compile(
        '^(?P<cmd>\S+)\s(?P<ast>\S+)\s' +
        '(?P<symbol>\S+)( (?P<instance>\S+))?\s' +
        '(?P<type>[^\t]+)\s(?P<path>[^\t]+)\s' +
        '(?P<line>\d+)\s(?P<col>\d+)\s' +
        '(?P<description>\".+\")?')

    # Methods
    @staticmethod
    def ensure_service(proj=""):
        # If service is running, do nothing
        if Idetools.service is not None and Idetools.service.poll() is None:
            return Idetools.service

        compiler = sublime.load_settings("nim.sublime-settings").get("nim_compiler_executable")
        if compiler == None or compiler == "": return

        Idetools.service = subprocess.Popen(
            compiler + " --verbosity:0 serve " +
            "--server.type:stdin " + proj,
            bufsize=1,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True)

        print("Nim CaaS now running")
        return Idetools.service

    @staticmethod
    def idetool(win, cmd, filename, line, col, dirtyFile="", extra=""):

        trackType = " --track:"
        filePath = filename
        projFile = Utility.get_nimproject(win)

        if projFile is None:
            projFile = filename

        workingDir = os.path.dirname(projFile)

        if dirtyFile != "":
            trackType = " --trackDirty:"
            filePath = dirtyFile + "," + filePath

        if True:  # TODO - use this when it's not broken in nim
            # Ensure IDE Tools service is running
            proc = Idetools.ensure_service(projFile)

            # Call the service
            args = "idetools" \
                + trackType \
                + '"' + filePath + "," + str(line) + "," + str(col) + '" ' \
                + cmd + extra

            print(args)

            proc.stdin.write(args + '\r\n')
            result = proc.stdout.readline()
            return result

        else:
            compiler = sublime.load_settings("nim.sublime-settings").get("nim_compiler_executable")
            if compiler == None or compiler == "": return ""

            args = compiler + " --verbosity:0 idetools " \
                + trackType \
                + '"' + filePath + "," + str(line) + "," + str(col) \
                + '" ' + cmd + ' "' + projFile + '"' + extra
            print(args)

            output = subprocess.Popen(args,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True,
                                      cwd=workingDir)

            result = ""

            temp = output.stdout.read()

            # Convert bytes to string
            result = temp.decode('utf-8')

            # print(output.stderr.read())
            output.wait()

        return result

    @staticmethod
    def parse(result):
        m = Idetools.pattern.match(result)

        if m is not None:
            cmd = m.group("cmd")

            if cmd == "def":
                return (m.group("symbol"), m.group("type"),
                        m.group("path"), m.group("line"),
                        m.group("col"), m.group("description"))

        else:
            None

        return None
