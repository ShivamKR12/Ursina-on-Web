from direct.dist import FreezeTool
import sys, os

# Changed to Python 3.13
if sys.version_info[:2] != (3, 13):
    sys.exit("Run this with Python 3.13, or edit this script")

# --- CUSTOM PATHS FOR YOUR WORKSPACE ---
WASM_PYTHON_DIR = "/workspaces/Ursina-on-Web/python313_wasm/usr/local"
PANDA_BUILT_DIR = "/workspaces/Ursina-on-Web/panda3d-webgl/built"

# Python built for target
PY_INCLUDE_DIR = WASM_PYTHON_DIR + "/include/python3.13"
PY_LIB_DIR = WASM_PYTHON_DIR + "/lib"

# Updated to libpython3.13.a
PY_LIBS = "libpython3.13.a", "libmpdec.a", "libexpat.a", "libHacl_Hash_SHA2.a"

# Python extension modules
PY_STDLIB_DIR = PY_LIB_DIR + "/python3.13"
PY_MODULE_DIR = PY_STDLIB_DIR + "/lib-dynload"
PY_MODULES = []

# Panda modules / libraries
PANDA_MODULES = ["core", "direct"]
PANDA_LIBS = ["libpanda", "libpandaexpress", "libp3dtool", "libp3dtoolconfig", "libp3webgldisplay", "libp3direct", "libp3openal_audio"]
PANDA_STATIC = True # built with --static

# Increase this when emscripten complains about running out of memory
INITIAL_HEAP = 83886080
STACK_SIZE = 1048576

# Increase this to get useful debugging info when crashes occur
ASSERTIONS = 2

# Files to preload into the virtual filesystem
PRELOAD_FILES = [
    #"models/environment.bam",
    "models/panda-model.bam",
    "models/panda-walk4.bam",
    "music/musicbox.ogg",
    #"music/openclose.ogg",
    "models/MusicBox.bam",
    "models/box.jpg",
    "models/panda.jpg",
]
PRELOAD_FILES += [
    "models/plane.bam",
    "textures/asteroid1.png",
    "textures/asteroid2.png",
    "textures/asteroid2.png",
    "textures/asteroid3.png",
    "textures/bullet.png",
    "textures/ship.png",
    #"textures/stars.jpg",
]
#PRELOAD_FILES = []

ASYNCIFY_ADD = [
    'task_manager_poll',
    'AsyncTaskManager::poll*',
    'AsyncTaskChain::poll*',
    'AsyncTaskChain::do_poll*',
    'AsyncTaskChain::service_one_task*',
    'AsyncTask::unlock_and_do_task*',
    'VirtualFileSystem::consider_match*',
    'VirtualFileSystem::do_get_file*',
    'VirtualFileSystem::get_file*',
]

ASYNCIFY_REMOVE = [
    'dlopen',
    'Dtool_*',
]

ASYNCIFY_IMPORTS = []

class EmscriptenEnvironment:
    platform = 'emscripten'

    pythonInc = PY_INCLUDE_DIR
    pythonLib = ""
    for lib in PY_LIBS:
        lib_path = PY_LIB_DIR + "/" + lib
        if os.path.isfile(lib_path):
            pythonLib += lib_path + " "

    # Updated to .cpython-313.o
    modStr = " ".join((os.path.join(PY_MODULE_DIR, a + ".cpython-313.o") for a in PY_MODULES))

    pandaFlags = ""
    for mod in PANDA_MODULES:
        if PANDA_STATIC:
            # Updated to cpython-313-wasm32
            pandaFlags += f" {PANDA_BUILT_DIR}/lib/libpy.panda3d.{mod}.cpython-313-wasm32-emscripten.a"
        else:
            pandaFlags += f" {PANDA_BUILT_DIR}/panda3d/{mod}.cpython-313-wasm32-emscripten.o"

    for lib in PANDA_LIBS:
        pandaFlags += f" {PANDA_BUILT_DIR}/lib/{lib}.a"

    pandaFlags += f" -I{PANDA_BUILT_DIR}/include"
    pandaFlags += " -s USE_ZLIB=1 -s USE_VORBIS=1 -s USE_LIBPNG=1 -s USE_FREETYPE=1 -s USE_HARFBUZZ=1 -s USE_SQLITE3=1 -s USE_BZIP2=1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -s DISABLE_EXCEPTION_THROWING=0 "

    pandaFlags += " -s 'EXPORTED_RUNTIME_METHODS=[\"cwrap\"]'"

    for file in PRELOAD_FILES:
        pandaFlags += " --preload-file %s" % file

    asyncifyFlags = ""

    compileObj = f"emcc -O3 -fno-exceptions -fno-rtti -c -o %(basename)s.o %(filename)s -I{pythonInc}"
    linkExe = f"emcc --bind -O3 {asyncifyFlags} -s INITIAL_HEAP={INITIAL_HEAP} -s STACK_SIZE={STACK_SIZE} -s ASSERTIONS={ASSERTIONS} -s MAX_WEBGL_VERSION=2 -s NO_EXIT_RUNTIME=1 -fno-exceptions -fno-rtti -o %(basename)s.js %(basename)s.o  " + modStr + " " + pythonLib + " " + pandaFlags
    linkDll = f"emcc -O2 -shared -o %(basename)s.o %(basename)s.o {pythonLib}"

    # Paths to Python stuff.
    Python = None
    PythonIPath = pythonInc
    PythonVersion = "3.13" # Updated to 3.13

    suffix64 = ''
    dllext = ''
    arch = ''

    def compileExe(self, filename, basename, extraLink=[]):
        compile = self.compileObj % {
            'python' : self.Python,
            'filename' : filename,
            'basename' : basename,
            }
        print(compile, file=sys.stderr)
        if os.system(compile) != 0:
            raise Exception('failed to compile %s.' % basename)

        link = self.linkExe % {
            'python' : self.Python,
            'filename' : filename,
            'basename' : basename,
            }
        link += ' ' + ' '.join(extraLink)
        print(link, file=sys.stderr)
        if os.system(link) != 0:
            raise Exception('failed to link %s.' % basename)

    def compileDll(self, filename, basename, extraLink=[]):
        compile = self.compileObj % {
            'python' : self.Python,
            'filename' : filename,
            'basename' : basename,
            }
        print(compile, file=sys.stderr)
        if os.system(compile) != 0:
            raise Exception('failed to compile %s.' % basename)

        link = self.linkDll % {
            'python' : self.Python,
            'filename' : filename,
            'basename' : basename,
            'dllext' : self.dllext,
            }
        link += ' ' + ' '.join(extraLink)
        print(link, file=sys.stderr)
        if os.system(link) != 0:
            raise Exception('failed to link %s.' % basename)


freezer = FreezeTool.Freezer()
freezer.frozenMainCode = """
#include "emscriptenmodule.c"
#include "browsermodule.c"

#include "Python.h"
#include <emscripten.h>

extern PyObject *PyInit_core();
extern PyObject *PyInit_direct();

extern void init_libOpenALAudio();
extern void init_libpnmimagetypes();
extern void init_libwebgldisplay();

extern void task_manager_poll();

EMSCRIPTEN_KEEPALIVE void loadPython() {
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.pathconfig_warnings = 0;
    config.use_environment = 0;
    config.write_bytecode = 0;
    config.site_import = 0;
    config.user_site_directory = 0;
    config.buffered_stdio = 0;

    PyStatus status = Py_InitializeFromConfig(&config);
    if (!PyStatus_Exception(status)) {
        fprintf(stderr, "Python %s\\n", Py_GetVersion());

        EM_ASM({
            Module.setStatus('Importing Panda3D...');
            window.setTimeout(_loadPanda, 0);
        });
    }
    PyConfig_Clear(&config);
}

EMSCRIPTEN_KEEPALIVE void loadPanda() {
    PyObject *panda3d_module = PyImport_AddModule("panda3d");
    PyModule_AddStringConstant(panda3d_module, "__package__", "panda3d");
    PyModule_AddObject(panda3d_module, "__path__", PyList_New(0));

    PyObject *panda3d_dict = PyModule_GetDict(panda3d_module);

    PyObject *core_module = PyInit_core();
    PyDict_SetItemString(panda3d_dict, "core", core_module);

    PyObject *direct_module = PyInit_direct();
    PyDict_SetItemString(panda3d_dict, "direct", direct_module);

    PyObject *sys_modules = PySys_GetObject("modules");
    PyDict_SetItemString(sys_modules, "panda3d.core", core_module);
    PyDict_SetItemString(sys_modules, "panda3d.direct", direct_module);

    PyDict_SetItemString(sys_modules, "emscripten", PyInit_emscripten());
    PyDict_SetItemString(sys_modules, "browser", PyInit_browser());

    init_libOpenALAudio();
    init_libpnmimagetypes();
    init_libwebgldisplay();

    EM_ASM({
        Module.setStatus('Done!');
    });
}

EMSCRIPTEN_KEEPALIVE void stopPythonCode() {
    emscripten_cancel_main_loop();
    PyRun_SimpleString("import builtins, gc, sys\\nsys.modules.pop('__main__', None)\\nsys.modules.pop('direct.directbase.DirectStart', None)\\nif hasattr(builtins, 'base'):\\n    base.taskMgr.destroy()\\n    base.destroy()\\nif hasattr(builtins, 'cpMgr'):\\n    while cpMgr.get_num_explicit_pages():\\n        cpMgr.delete_explicit_page(cpMgr.get_explicit_page(0))\\nif hasattr(builtins, 'base'):\\n    del builtins.base\\nif hasattr(builtins, 'taskMgr'):\\n    del builtins.taskMgr\\ngc.collect()\\n");
}

// Add Paolo's setup function above runPythonCode
static void setup_ursina_emscripten(void)
{
    PyRun_SimpleString(
        "def _setup():\\n"
        "    from ursina import application\\n"
        "    from pathlib import Path\\n"
        "    ursina_assets = Path('.')\\n"
        "    game_assets   = Path('.')\\n"
        "    application.package_folder = ursina_assets\\n"
        "    application.asset_folder   = game_assets\\n"
        "    application.scenes_folder  = game_assets / 'scenes/'\\n"
        "    application.scripts_folder = game_assets / 'scripts/'\\n"
        "    application.fonts_folder   = game_assets / 'fonts/'\\n"
        "    application.internal_models_folder            = ursina_assets / 'models/'\\n"
        "    application.internal_models_compressed_folder = ursina_assets / 'models_compressed/'\\n"
        "    application.internal_scripts_folder           = ursina_assets / 'scripts/'\\n"
        "    application.internal_textures_folder          = ursina_assets / 'textures/'\\n"
        "    application.internal_fonts_folder             = ursina_assets / 'fonts/'\\n"
        "    application.internal_audio_folder             = ursina_assets / 'audio/'\\n"
        "_setup()\\n"
        "del _setup\\n"
    );
}

EMSCRIPTEN_KEEPALIVE void runPythonCode(char *codeToExecute) {
    // Run the Ursina patch BEFORE executing the user's web code!
    setup_ursina_emscripten();

    if (PyRun_SimpleString(codeToExecute)) {
        stopPythonCode();
    } else {
        emscripten_set_main_loop(&task_manager_poll, 0, 0);
        EM_ASM({
            document.getElementById('stop-button').disabled = false;
        });
    }
}

int
Py_FrozenMain(int argc, char **argv)
{
    EM_ASM({
        Module.setStatus('Starting Python...');
        window.setTimeout(_loadPython, 0);
    });

    return 0;
}
"""

freezer.moduleSearchPath = [PANDA_BUILT_DIR, PY_STDLIB_DIR, PY_MODULE_DIR]

freezer.cenv = EmscriptenEnvironment()
freezer.excludeModule('doctest')
freezer.excludeModule('difflib')
freezer.excludeModule('panda3d')

# YOU MUST TELL THE FREEZER TO BUNDLE URSINA!
freezer.addModule('ursina')

freezer.addModule('__main__', filename="main.py")

freezer.done(addStartupModules=True)
freezer.generateCode("editor", compileToExe=True)
