# -*- coding: utf-8 -*-1

"""Tests of base classes."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import raises

from ..base import (BaseViewModel, HTMLViewModel, WidgetCreator,
                    BaseGUI, BaseSession,
                    )
from ..qt import _close_qt_after, qt_app, QtGui
from ...utils import EventEmitter


#------------------------------------------------------------------------------
# Base tests
#------------------------------------------------------------------------------

_DURATION = .5


def test_base_view_model():
    class MyViewModel(BaseViewModel):
        _view_name = 'main_window'
        _imported_params = ('text',)

        def _create_view(self, text='', size=None):
            view = QtGui.QMainWindow()
            view.setWindowTitle(text)
            if size is not None:
                view.resize(*size)
            return view

    size = (400, 20)
    text = 'hello'

    with qt_app():
        vm = MyViewModel(text=text, size=size)
        _close_qt_after(vm, _DURATION)
        vm.show()
        assert vm.view.windowTitle() == text
        assert vm.text == text
        assert vm.size == size
        assert (vm.view.width(), vm.view.height()) == size


def test_widget_creator():

    class MyWidget(EventEmitter):
        """Mock widget."""
        def __init__(self, param=None):
            super(MyWidget, self).__init__()
            self.name = 'my_widget'
            self._shown = False
            self.param = param

        @property
        def shown(self):
            return self._shown

        def close(self, e=None):
            self.emit('close', e)
            self._shown = False

        def show(self):
            self._shown = True

    widget_classes = {'my_widget': MyWidget}

    wc = WidgetCreator(widget_classes=widget_classes)
    assert not wc.get()
    assert not wc.get('my_widget')

    with raises(ValueError):
        wc.add('my_widget_bis')

    for show in (False, True):
        w = wc.add('my_widget', show=show, param=show)
        assert len(wc.get()) == 1
        assert len(wc.get('my_widget')) == 1

        assert w.shown is show
        assert w.param is show
        w.show()
        assert w.shown

        w.close()
        assert not wc.get()
        assert not wc.get('my_widget')


def test_base_gui():
    vm_classes = {'my_widget': HTMLViewModel}

    with qt_app():
        gui = BaseGUI(vm_classes=vm_classes,
                      )
        gui.add_view('my_widget', html='hello')
        _close_qt_after(gui, _DURATION)
        gui.show()
