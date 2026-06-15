#!/usr/bin/env python3
"""mgui.py — Graphical front-end for the mUtils movie management toolkit.

Launches a tabbed Tkinter window with one tab per tool.  Directory fields
use the operating system's native file-chooser dialog.  Each tool runs in
a background thread so the UI stays responsive during long operations.

Usage::

    python3 mgui.py
"""

import sys
import threading

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
except ImportError:
    sys.exit(
        'tkinter is required but not installed.\n'
        '  macOS:   brew install python-tk\n'
        '  Ubuntu:  sudo apt install python3-tk\n'
        '  Windows: re-run the Python installer and enable Tcl/Tk\n'
    )

# Import logic functions (not main()) from each tool so the originals are
# never modified and can still be used standalone.
import mdiffer
import mremover
import mrenamer
import msymlinker


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_task(fn):
    """Run *fn* and return displayable text.

    :param fn: Zero-argument callable to run.
    :type fn: callable
    :returns: Text returned by the callable, or an error message.
    :rtype: str
    """
    try:
        result = fn()
    except SystemExit:
        return ''
    except Exception as exc:
        return 'Error: {}\n'.format(exc)
    return '' if result is None else str(result)


# ── Main application window ───────────────────────────────────────────────────

class MUtilsApp(tk.Tk):
    """Root window for the mUtils GUI."""

    def __init__(self):
        super().__init__()
        self.title('mUtils — Movie Management Tools')
        self.geometry('740x560')
        self.minsize(640, 480)
        self.resizable(True, True)
        self._apply_theme()
        self._build_ui()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        """Apply the best available ttk theme for a native look."""
        style = ttk.Style(self)
        preferred = ['aqua', 'vista', 'clam', 'alt', 'default']
        available = style.theme_names()
        for name in preferred:
            if name in available:
                style.theme_use(name)
                break

        style.configure('Run.TButton', font=('', 10, 'bold'), padding=6)
        style.configure('Header.TLabel', font=('', 9), foreground='gray')

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the tabbed notebook and status bar."""
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=(10, 4))

        self._build_mdiffer_tab(notebook)
        self._build_mremover_tab(notebook)
        self._build_mrenamer_tab(notebook)
        self._build_msymlinker_tab(notebook)

        # Status bar
        self._status_var = tk.StringVar(value='Ready.')
        status = ttk.Label(self, textvariable=self._status_var,
                           anchor='w', relief='sunken', padding=(6, 2))
        status.pack(fill='x', side='bottom', padx=10, pady=(0, 6))

    # ── Reusable widget builders ──────────────────────────────────────────────

    def _dir_row(self, parent, label, row):
        """Add a directory-picker row (label + entry + Browse button).

        :param parent: Parent widget to attach the row to.
        :param label: Text label displayed to the left of the entry.
        :type label: str
        :param row: Grid row index.
        :type row: int
        :returns: StringVar bound to the entry widget.
        :rtype: tk.StringVar
        """
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky='w', pady=4, padx=(0, 6))
        var = tk.StringVar()
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky='ew', pady=4)

        def browse():
            path = filedialog.askdirectory(title='Select: ' + label)
            if path:
                var.set(path)

        ttk.Button(parent, text='Browse…', command=browse, width=9).grid(
            row=row, column=2, padx=(6, 0), pady=4)
        return var

    def _text_row(self, parent, label, row, default='', width=20):
        """Add a plain text-entry row.

        :param parent: Parent widget.
        :param label: Label text.
        :type label: str
        :param row: Grid row index.
        :type row: int
        :param default: Pre-filled default value.
        :type default: str
        :param width: Entry widget character width.
        :type width: int
        :returns: StringVar bound to the entry widget.
        :rtype: tk.StringVar
        """
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky='w', pady=4, padx=(0, 6))
        var = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=var, width=width).grid(
            row=row, column=1, sticky='w', pady=4)
        return var

    def _output_area(self, parent):
        """Add a scrolled output text area inside a labelled frame.

        :param parent: Parent widget.
        :returns: The ScrolledText widget.
        :rtype: scrolledtext.ScrolledText
        """
        frame = ttk.LabelFrame(parent, text='Output', padding=4)
        frame.pack(fill='both', expand=True, padx=0, pady=(6, 0))
        out = scrolledtext.ScrolledText(
            frame, height=10, state='disabled',
            font=('Courier', 10), wrap='word', relief='flat')
        out.pack(fill='both', expand=True)
        return out

    def _write(self, widget, text):
        """Append *text* to a disabled ScrolledText widget (thread-safe).

        :param widget: Target ScrolledText widget.
        :param text: Text to append.
        :type text: str
        """
        widget.configure(state='normal')
        widget.insert('end', text)
        widget.see('end')
        widget.configure(state='disabled')

    def _clear(self, widget):
        """Clear all text from a disabled ScrolledText widget.

        :param widget: Target ScrolledText widget.
        """
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.configure(state='disabled')

    def _run(self, fn, out_widget, btn):
        """Execute *fn* in a background thread, routing text to *out_widget*.

        Disables *btn* while running and restores it on completion.

        :param fn: Zero-argument callable containing the tool logic.
        :type fn: callable
        :param out_widget: ScrolledText widget that receives the output.
        :param btn: Button widget to disable during execution.
        """
        btn.configure(state='disabled')
        self._status_var.set('Running…')

        def worker():
            result = _run_task(fn)
            self.after(0, self._write, out_widget, result)
            self.after(0, self._status_var.set, 'Done.')
            self.after(0, btn.configure, {'state': 'normal'})

        threading.Thread(target=worker, daemon=True).start()

    # ── mdiffer tab ───────────────────────────────────────────────────────────

    def _build_mdiffer_tab(self, notebook):
        """Build the mdiffer tab."""
        outer = ttk.Frame(notebook, padding=12)
        notebook.add(outer, text='  mdiffer  ')

        ttk.Label(outer, text='Find movies present in both directories.',
                  style='Header.TLabel').pack(anchor='w', pady=(0, 8))

        form = ttk.Frame(outer)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)

        self._diff_primary = self._dir_row(form, 'Primary Directory:', 0)
        self._diff_secondary = self._dir_row(form, 'Secondary Directory:', 1)

        btn = ttk.Button(outer, text='Find Duplicates',
                         style='Run.TButton', command=lambda: self._run_mdiffer(btn))
        btn.pack(pady=8)

        self._diff_out = self._output_area(outer)

    def _run_mdiffer(self, btn):
        """Validate inputs and kick off the mdiffer task."""
        primary = self._diff_primary.get().strip()
        secondary = self._diff_secondary.get().strip()
        if not primary or not secondary:
            messagebox.showwarning('Missing Input',
                                   'Please select both directories.')
            return
        self._clear(self._diff_out)

        def task():
            result = mdiffer.run_diff(primary, secondary)
            return mdiffer.format_diff_result(result)

        self._run(task, self._diff_out, btn)

    # ── mremover tab ─────────────────────────────────────────────────────────

    def _build_mremover_tab(self, notebook):
        """Build the mremover tab."""
        outer = ttk.Frame(notebook, padding=12)
        notebook.add(outer, text='  mremover  ')

        ttk.Label(outer, text='Delete all files with a given extension inside a directory.',
                  style='Header.TLabel').pack(anchor='w', pady=(0, 8))

        form = ttk.Frame(outer)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)

        self._rem_dir = self._dir_row(form, 'Source Directory:', 0)
        self._rem_ext = self._text_row(form, 'Extension:', 1, default='.nfo', width=12)

        self._rem_dryrun = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form, text='Dry run — preview only, no files will be deleted',
            variable=self._rem_dryrun
        ).grid(row=2, column=0, columnspan=3, sticky='w', pady=6)

        btn = ttk.Button(outer, text='Remove Files',
                         style='Run.TButton', command=lambda: self._run_mremover(btn))
        btn.pack(pady=8)

        self._rem_out = self._output_area(outer)

    def _run_mremover(self, btn):
        """Validate inputs, confirm if not dry-run, then execute mremover."""
        src = self._rem_dir.get().strip()
        ext = self._rem_ext.get().strip()
        dry_run = self._rem_dryrun.get()

        if not src:
            messagebox.showwarning('Missing Input', 'Please select a source directory.')
            return
        if not ext:
            messagebox.showwarning('Missing Input', 'Please enter a file extension.')
            return
        if not dry_run:
            if not messagebox.askyesno(
                    'Confirm Deletion',
                    'This will permanently delete all *{} files.\n\nContinue?'.format(ext)):
                return

        self._clear(self._rem_out)

        def task():
            result = mremover.remover(src, ext, dry_run=dry_run)
            return mremover.format_remove_result(result)

        self._run(task, self._rem_out, btn)

    # ── mrenamer tab ─────────────────────────────────────────────────────────

    def _build_mrenamer_tab(self, notebook):
        """Build the mrenamer tab."""
        outer = ttk.Frame(notebook, padding=12)
        notebook.add(outer, text='  mrenamer  ')

        ttk.Label(outer,
                  text='Rename scene-style movie folders and files to "Title (Year)" format.',
                  style='Header.TLabel').pack(anchor='w', pady=(0, 8))

        form = ttk.Frame(outer)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)

        self._ren_dir = self._dir_row(form, 'Source Directory:', 0)

        btn = ttk.Button(outer, text='Rename',
                         style='Run.TButton', command=lambda: self._run_mrenamer(btn))
        btn.pack(pady=8)

        self._ren_out = self._output_area(outer)

    def _run_mrenamer(self, btn):
        """Validate input and execute mrenamer."""
        src = self._ren_dir.get().strip()
        if not src:
            messagebox.showwarning('Missing Input', 'Please select a source directory.')
            return
        self._clear(self._ren_out)

        def task():
            result = mrenamer.renamer(src)
            return mrenamer.format_rename_result(result)

        self._run(task, self._ren_out, btn)

    # ── msymlinker tab ────────────────────────────────────────────────────────

    def _build_msymlinker_tab(self, notebook):
        """Build the msymlinker tab."""
        outer = ttk.Frame(notebook, padding=12)
        notebook.add(outer, text='  msymlinker  ')

        ttk.Label(outer, text='Create a soft symlink from a new location back to the original.',
                  style='Header.TLabel').pack(anchor='w', pady=(0, 8))

        form = ttk.Frame(outer)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)

        self._sym_src = self._dir_row(form, 'Source Directory:', 0)

        ttk.Label(form, text='Original Name:').grid(
            row=1, column=0, sticky='w', pady=4, padx=(0, 6))
        self._sym_old = tk.StringVar()
        ttk.Entry(form, textvariable=self._sym_old).grid(
            row=1, column=1, columnspan=2, sticky='ew', pady=4)

        self._sym_dest = self._dir_row(form, 'Destination Directory:', 2)

        ttk.Label(form, text='Symlink Name:').grid(
            row=3, column=0, sticky='w', pady=4, padx=(0, 6))
        self._sym_new = tk.StringVar()
        ttk.Entry(form, textvariable=self._sym_new).grid(
            row=3, column=1, columnspan=2, sticky='ew', pady=4)

        btn = ttk.Button(outer, text='Create Symlink',
                         style='Run.TButton', command=lambda: self._run_msymlinker(btn))
        btn.pack(pady=8)

        self._sym_out = self._output_area(outer)

    def _run_msymlinker(self, btn):
        """Validate inputs and execute msymlinker."""
        src = self._sym_src.get().strip()
        old_name = self._sym_old.get().strip()
        dest = self._sym_dest.get().strip()
        new_name = self._sym_new.get().strip()

        if not all([src, old_name, dest, new_name]):
            messagebox.showwarning('Missing Input', 'Please fill in all four fields.')
            return
        self._clear(self._sym_out)

        def task():
            result = msymlinker.linker(src, old_name, dest, new_name)
            return msymlinker.format_link_result(result)

        self._run(task, self._sym_out, btn)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    """Launch the mUtils graphical interface."""
    app = MUtilsApp()
    app.mainloop()


if __name__ == '__main__':
    main()
