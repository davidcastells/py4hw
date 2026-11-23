import tkinter 
import tkinter.font
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import os
from .base import Logic
from .schematic import Schematic
    
import sys
import importlib

import queue
import threading
import tkinter



class GuiManager:
    """
    In tkinter a single Tk root is used for all windows.
    Central owner of the single Tk root and event loop for py4hw.
    """

    _default = None
    _default_lock = threading.Lock()

    @classmethod
    def default(cls) -> "GuiManager":
        """Shared manager used by windows that are not given one explicitly."""
        with cls._default_lock:
            if cls._default is None:
                cls._default = cls()
            return cls._default

    def __init__(self, poll_ms: int = 50):
        self.poll_ms = poll_ms
        self._queue: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.root: tkinter.Tk | None = None
        self._windows: list[tkinter.Toplevel] = []
        self._lock = threading.Lock()
        self._error: BaseException | None = None

    def start(self) -> None:
        """Start the dedicated GUI thread if not already running."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._ready.clear()
        self._error = None
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="py4hw-GuiThread"
        )
        self._thread.start()
        self._ready.wait()
        if self._error is not None:
            raise self._error

    def is_gui_thread(self) -> bool:
        return self._thread is not None and threading.get_ident() == self._thread.ident

    def call_soon(self, fn) -> None:
        """Thread-safe: run fn() in the GUI thread (at the next poll)."""
        self.start()
        self._queue.put(fn)

    def _run(self) -> None:
        try:
            self.root = tkinter.Tk()
            self.root.withdraw()  # keep hidden dummy root; windows are Toplevels
            self.root.after(self.poll_ms, self._drain_queue)
        except BaseException as exc:
            self._error = exc
            self._ready.set()
            return

        self._ready.set()
        try:
            self.root.mainloop()
        finally:
            self.root = None
            with self._lock:
                self._windows.clear()

    def _drain_queue(self) -> None:
        if self.root is None:
            return
        try:
            while True:
                try:
                    task = self._queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    task()
                except Exception:
                    # one failing task must not kill the polling loop
                    import traceback
                    traceback.print_exc()
        finally:
            if self.root is not None:
                self.root.after(self.poll_ms, self._drain_queue)

    def register_window(self, win: tkinter.Toplevel, on_close=None) -> None:
        """Track an open window and wire its cleanup on destroy."""
        with self._lock:
            if win not in self._windows:
                self._windows.append(win)

        def _handle_destroy(event):
            if event.widget is win:
                with self._lock:
                    if win in self._windows:
                        self._windows.remove(win)
                if on_close is not None:
                    on_close()

        win.bind("<Destroy>", _handle_destroy, add="+")

    @staticmethod
    def _toplevel_of(obj):
        tk_win = obj.toplevel if hasattr(obj, "toplevel") else obj
        return tk_win if isinstance(tk_win, tkinter.Toplevel) else None

    def open_window(self, factory, *, blocking: bool = False, modal: bool = False):
        """
        Create a Toplevel via `factory(root, manager)` on the GUI thread.
        - `blocking=False`: returns immediately with the created window/controller.
        - `blocking=True`: waits until that window is destroyed, while keeping
          the GUI event loop alive for other windows.
        """
        self.start()

        created_box = {}
        closed_event = threading.Event()
        done_creating = threading.Event()

        def _create_on_gui_thread():
            try:
                win_obj = factory(self.root, self)
                created_box["obj"] = win_obj

                tk_win = self._toplevel_of(win_obj)
                if tk_win is not None:
                    self.register_window(tk_win, on_close=closed_event.set)
                    if modal:
                        # No transient(self.root): the root is withdrawn, and on some
                        # platforms a transient of a withdrawn window is hidden too.
                        tk_win.grab_set()
                else:
                    closed_event.set()
            except BaseException as exc:
                created_box["error"] = exc
                closed_event.set()
            finally:
                done_creating.set()

        if self.is_gui_thread():
            _create_on_gui_thread()
            if "error" in created_box:
                raise created_box["error"]
            win_obj = created_box["obj"]
            tk_win = self._toplevel_of(win_obj)
            if blocking and tk_win is not None:
                tk_win.wait_window()
            return win_obj

        self._queue.put(_create_on_gui_thread)
        # wait with a timeout so a dead GUI thread cannot hang the caller forever
        while not done_creating.wait(0.2):
            if self._thread is None or not self._thread.is_alive():
                raise RuntimeError("py4hw GUI thread is not running")
        if "error" in created_box:
            raise created_box["error"]

        if blocking:
            # short timeouts keep Ctrl-C working in the calling thread
            while not closed_event.wait(0.2):
                pass

        return created_box["obj"]
        
def get_package_path(package_name):
    if sys.version_info >= (3, 9):
        import importlib.resources as resources
        return resources.files(package_name)
    else:
        import importlib_resources as resources
        return resources.path(package_name, '')

def get_resource_path(package_name, resource_name):
    if sys.version_info >= (3, 9):
        import importlib.resources as resources
        package_path = resources.files(package_name)
        return package_path / resource_name
    else:
        import importlib.resources as resources
        with resources.path(package_name, resource_name) as resource_path:
            return resource_path
    
def getIcon(path):
    #script_directory = os.path.dirname(os.path.abspath(__file__))
    #icon_path = os.path.join(script_directory, path)
    
    icon = Image.open(path)
    icon = ImageTk.PhotoImage(icon)
    return icon

def getResourceIcon(name):
    path = get_resource_path('py4hw' , name)

    return getIcon(path)



class Workbench():
    '''
    This builds an interactive simulation GUI

    +----------------------+----------------------------+
    | Circuit Hierarchy    | Selected Circuit Interface |
    | self.hierarchyTree   | self.interfacePane         |
    |                      +----------------------------+
    |                      | Selected Circuit Schematic |
    |                      | self.schematicAreaPane     |
    +----------------------+----------------------------+

    The window is a Toplevel created in the py4hw GUI thread through the GuiManager.
    Everything that touches Tk (building, refreshing, callbacks) runs in that thread.
    '''

    def __init__(self, sys: Logic, blocking=False, manager=None, liveUpdate=True):
        """
        blocking   : False (default) -> return immediately, the window lives in the GUI thread.
                     True            -> return when the window is closed (other windows keep working).
        manager    : GuiManager to use; defaults to GuiManager.default().
        liveUpdate : register as simulator listener so the window refreshes when the
                     simulation advances from outside (e.g. from your script).
        """
        self.sys = sys
        self.detailObj = None

        self.pollMs = 200          # refresh is expensive (schematic is rebuilt), so poll gently
        self._dirty = False        # set by the simulator thread, consumed by the GUI thread
        self._closed = False
        self._closed_event = threading.Event()

        self.toplevel = None
        self.root = None

        # Register from the calling thread; the callback only sets a flag, so it is thread safe.
        if liveUpdate:
            self.sys.getSimulator().addListener(self)

        try:
            mgr = manager if manager is not None else GuiManager.default()
            mgr.open_window(lambda r, m: self._create(tkinter.Toplevel(r)),
                            blocking=blocking)
        except BaseException:
            self._closed = True    # stop reacting to the simulator
            raise

    def _create(self, win):
        """Build the window contents into `win`. Must run in the GUI thread."""
        self.toplevel = win
        self.root = win
        self._build()
        return self                # exposes .toplevel, which GuiManager tracks

    def wait(self):
        """Block until the window is closed (useful at the end of a script)."""
        while not self._closed_event.wait(0.2):
            pass

    def _build(self):
        root = self.root
        root.title('py4hw Interactive Workbench')

        ttk.Style().configure("Treeview", fg="light yellow")
        font = tkinter.font.Font(size=8)
        #ttk.Style().configure("Prolepsis.Treeview", font=font)

        self.topPane = PanedWindow(root, orient=HORIZONTAL)

        self.hierarchyPane = Frame(self.topPane)
        self.topPane.add(self.hierarchyPane)

        self.buttonPane = Frame(self.hierarchyPane)

        self.txtClocks = tkinter.StringVar(value='1')
        txtClocks = ttk.Entry(self.buttonPane, width=10, textvariable=self.txtClocks)
        txtClocks.pack(side=tkinter.LEFT, padx=10, pady=(10, 5))

        btnClock = ttk.Button(self.buttonPane, text="Clock", command=self.guiClk)
        btnClock.pack(side=tkinter.RIGHT, padx=(10, 0), pady=(10, 5))

        self.buttonPane.pack(side=tkinter.TOP)

        self.createHierarchyTree()

        self.rightPane = PanedWindow(self.topPane, orient=VERTICAL, relief=SUNKEN, width=100, height=100)
        self.topPane.add(self.rightPane)

        self.interfacePane = PanedWindow(self.rightPane, relief=SUNKEN, width=100, height=100)

        self.schematicAreaPane = PanedWindow(self.rightPane, orient=VERTICAL, relief=SUNKEN, width=100, heigh=20)
        self.schematicToolbarPane = Frame(self.schematicAreaPane)

        self.rightPane.add(self.interfacePane)
        self.rightPane.add(self.schematicAreaPane)
        self.schematicAreaPane.add(self.schematicToolbarPane)

        # keep references, otherwise Tk images get garbage collected
        self.icon_zo = getResourceIcon('zoomout24.png')
        self.icon_zi = getResourceIcon('zoomin24.png')

        btnZoomIn = ttk.Button(self.schematicToolbarPane, image=self.icon_zi, text="Zoom in", command=self.guiZoomIn)
        btnZoomOut = ttk.Button(self.schematicToolbarPane, image=self.icon_zo, text="Zoom out", command=self.guiZoomOut)

        btnZoomIn.pack(side=tkinter.LEFT)
        btnZoomOut.pack(side=tkinter.LEFT)

        self.schematicPane = PanedWindow(self.schematicAreaPane, relief=SUNKEN, width=100, height=100)
        self.schematicAreaPane.add(self.schematicPane)

        self.circuitDetail(None)

        self.topPane.pack(fill=BOTH, expand=True)

        # --- live updates ----------------------------------------------
        self.topPane.bind('<Destroy>', self._on_destroy)
        self.root.after(self.pollMs, self._poll)

    # ------------------------------------------------------------------
    # simulator listener / refresh
    # ------------------------------------------------------------------
    def simulatorUpdated(self, *args, **kwargs):
        """
        Called by the simulator, possibly from another thread. It must NOT touch Tk,
        so it only raises a flag; the GUI thread picks it up in _poll().
        """
        self._dirty = True

    def _poll(self):
        # runs in the GUI thread
        if self._closed:
            return
        try:
            if self._dirty:
                self._dirty = False
                self.refresh()
        except Exception:
            # a failing refresh must not kill the polling loop
            import traceback
            traceback.print_exc()
        finally:
            if not self._closed:
                self.root.after(self.pollMs, self._poll)

    def _on_destroy(self, event):
        if event.widget is self.topPane:
            self._closed = True
            self._closed_event.set()

    def refresh(self):
        """
        TODO: We do the dirty trick to recreate all the table to just
        update the circuit status. We will try to do better in the future
        """
        if (self.detailObj != None):
            self.setCircuitDetail(self.detailObj)

    # ------------------------------------------------------------------
    # button callbacks (GUI thread)
    # ------------------------------------------------------------------
    def guiClk(self):
        clks = int(self.txtClocks.get())
        sim = self.sys.getSimulator()
        sim.clk(clks)
        # we are already in the GUI thread: update now instead of waiting for the poll
        self._dirty = False
        self.refresh()

    def guiZoomOut(self):
        self.schematicDiagram.scale("all", 0, 0, 0.9, 0.9)

    def guiZoomIn(self):
        self.schematicDiagram.scale("all", 0, 0, 1.1, 1.1)

    # ------------------------------------------------------------------
    # circuit detail
    # ------------------------------------------------------------------
    def circuitDetail(self, obj: Logic):

        # this is called just once now (?)
        print('Circuit detail on ', obj)

        # Create the Circuit Interface pane
        # @todo we are creating this every time we focus on a circuit, could we
        # just create it once and clear the tree view and populate it as necessary ?
        self.detail_tv = ttk.Treeview(self.interfacePane)

        detail_tv = self.detail_tv
        self.interfacePane.add(detail_tv)

        detail_tv.pack(fill=BOTH, expand=YES)

        detail_tv.config(columns=['direction', 'width', 'value'])
        detail_tv.config(displaycolumns=[0, 1, 2])

        detail_tv.heading('#0', text='Name')
        detail_tv.heading('direction', text='Direction')
        detail_tv.heading('width', text='Width')
        detail_tv.heading("value", text="Value")

        detail_tv.column("#0", minwidth=0, width=100)
        detail_tv.column('direction', minwidth=0, width=100)
        detail_tv.column('width', minwidth=0, width=100)
        detail_tv.column("value", minwidth=0, width=100)

        detail_tv.config(selectmode=tkinter.BROWSE)
        detail_tv.tag_configure("ally", background="green")
        detail_tv["style"] = "Prolepsis.Treeview"

        detail_tv.bind("<Control-c>", self.copy_selected_text)

        if (obj == None):
            return

        self.setCircuitDetail(obj)

    def copy_selected_text(self, event=None):
        selected_items = self.detail_tv.selection()  # Get IDs of all selected items

        if not selected_items:
            print("No row selected to copy.")
            return

        text_to_copy = []
        for item_id in selected_items:
            # 'values' returns a tuple of the data in each column for that row
            row_values = self.detail_tv.item(item_id, 'values')

            if row_values:
                # Tab separated: useful for pasting into spreadsheet applications.
                text_to_copy.append("\t".join(map(str, row_values)))
            else:
                print(f"Warning: Selected item {item_id} has no values.")

        if not text_to_copy:
            print("No content found in selected rows to copy.")
            return

        self.detail_tv.clipboard_clear()
        self.detail_tv.clipboard_append("\n".join(text_to_copy))
        # Force Tkinter to update the clipboard immediately
        self.detail_tv.update()

        print(f"Copied {len(selected_items)} row(s) to clipboard.")

    def debugTkinterHierarchy(self, obj, ii):
        indent = '|' * ii + '+'
        print('[INFO] {} tkinter obj {} {}'.format(indent, type(obj), obj._name if (hasattr(obj, '_name')) else ''))

        try:
            for child in obj.children.values():
                self.debugTkinterHierarchy(child, ii + 1)
        except:
            pass

    def setCircuitDetail(self, obj: Logic):

        if (obj != None):
            for pane in self.schematicPane.panes():
                self.schematicPane.forget(pane)

            if (obj.isStructural()):
                # ignore non structural circuits
                sch = Schematic(obj, render='tkinter', parent=self.schematicPane, showValues=True)

                sch.drawAll()
                self.schematicDiagram = sch.canvas.canvas
                self.schematicPane.add(self.schematicDiagram)
            elif (hasattr(obj, 'tkinter_gui')):
                sch = obj.tkinter_gui(self.schematicPane)
                self.schematicPane.add(sch)

        self.detailObj = obj
        self.detail_tv.delete(*self.detail_tv.get_children())

        detail_tv = self.detail_tv

        visitedPorts = []
        for source in obj.sources:
            sWidth = ''
            sValue = ''
            in_id = detail_tv.insert("", tkinter.END, text=source.name, values=[sWidth, sValue], open=True)

            for inp in source.ports:
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                port_id = detail_tv.insert(in_id, tkinter.END, text=inp.name, values=['in', sWidth, sValue], open=True)
                visitedPorts.append(inp)

        for sink in obj.sinks:
            sWidth = ''
            sValue = ''
            in_id = detail_tv.insert("", tkinter.END, text=sink.name, values=[sWidth, sValue], open=True)

            for inp in sink.ports:
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                port_id = detail_tv.insert(in_id, tkinter.END, text=inp.name, values=['out', sWidth, sValue], open=True)
                visitedPorts.append(inp)

        for inp in obj.inPorts:
            if (inp not in visitedPorts):
                sWidth = inp.wire.getWidth()
                sValue = hex(inp.wire.get())
                in_id = detail_tv.insert("", tkinter.END, text=inp.name, values=['in', sWidth, sValue], open=True)

        for outp in obj.outPorts:
            if (outp not in visitedPorts):
                sWidth = outp.wire.getWidth()
                sValue = hex(outp.wire.get())
                in_id = detail_tv.insert("", tkinter.END, text=outp.name, values=['out', sWidth, sValue], open=True)

    def callback(self, event):
        tvid = self.hierarchyTree.focus()
        obj = self.map_id_obj[tvid]
        self.setCircuitDetail(obj)

    # ------------------------------------------------------------------
    # hierarchy tree
    # ------------------------------------------------------------------
    def populateTree(self, tv, tvid, obj: Logic):
        for child in obj.children.values():
            instanceName = child.name
            circuitType = 'Structural'
            if (child.isClockable()):
                circuitType = 'Clockable'
            elif (child.isPropagatable()):
                circuitType = 'Propagatable'
            childid = tv.insert(tvid, tkinter.END, text=type(child).__name__,
                                values=[instanceName, circuitType, child.getFullPath()], tags=["ally", "char"])
            self.map_id_obj[childid] = child
            self.populateTree(tv, childid, child)

    def createHierarchyTree(self):
        self.hierarchyTree = ttk.Treeview(self.hierarchyPane)

        tv = self.hierarchyTree
        self.map_id_obj = {}

        tv.bind('<<TreeviewSelect>>', self.callback)
        tv.pack(fill=BOTH, expand=YES)

        dc_iid = tv.insert("", tkinter.END, text="HWSystem", values=['Top', 'Top level'], open=True)

        self.map_id_obj[dc_iid] = self.sys

        self.populateTree(tv, dc_iid, self.sys)

        print(tv.cget("displaycolumns"))
        tv.config(columns=['instance', 'type'])
        tv.config(displaycolumns=[0, 1])
        tv.heading('instance', text='Instance name')
        tv.heading("type", text="Type")
        tv.heading("#0", text="Name")
        tv.config(selectmode=tkinter.BROWSE)

        tv["style"] = "Prolepsis.Treeview"
        print(ttk.Style().lookup("Prolepsis.Treeview", "background"))