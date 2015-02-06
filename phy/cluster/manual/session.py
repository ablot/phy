# -*- coding: utf-8 -*-

"""Session structure."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import numpy as np

from ._history import GlobalHistory
from .clustering import Clustering
from .cluster_view import ClusterView
from .cluster_metadata import ClusterMetadata
from .selector import Selector
from ...io.base_model import BaseModel
from ...plot.waveforms import WaveformView
from ...notebook.utils import load_css


#------------------------------------------------------------------------------
# View manager
#------------------------------------------------------------------------------

class ViewManager(object):
    """Manage several views."""
    def __init__(self):
        self._views = []

    def register(self, view):
        """Register a view."""
        self._views.append(view)

    def unregister(self, view):
        """Unregister a view."""
        view.close()
        if view in self._views:
            self._views.remove(view)

    @property
    def views(self):
        return self._views


#------------------------------------------------------------------------------
# Session class
#------------------------------------------------------------------------------

class Session(object):
    """Provide all user-exposed actions for a manual clustering session."""

    def __init__(self, model):
        if not isinstance(model, BaseModel):
            raise ValueError("'model' must be an instance of a "
                             "class deriving from BaseModel.")
        self._global_history = GlobalHistory()
        self._view_manager = ViewManager()
        # Set the model and initialize the session.
        self.model = model
        self._update_after_load()

    # Controller.
    # -------------------------------------------------------------------------

    def _update_after_load(self):
        """Update the session after new data has been loaded."""
        # Update the Selector and Clustering instances using the Model.
        spike_clusters = self.model.spike_clusters
        self.selector = Selector(spike_clusters, n_spikes_max=100)
        self.clustering = Clustering(spike_clusters)
        self.cluster_metadata = self.model.cluster_metadata
        # Reinitialize all existing views.
        for view in self._view_manager.views:
            if isinstance(view, WaveformView):
                self._update_waveforms_after_load(view)
            view.update()

    def _update_after_select(self):
        """Update the views after the selection has changed."""
        for view in self._view_manager.views:
            if isinstance(view, WaveformView):
                self._update_waveforms_after_select(view)
            view.update()

    def _update_after_cluster(self, up, add_to_stack=True):
        """Update the session after the clustering has changed."""

        # TODO: Update the similarity matrix.
        # stats.update(up)

        # TODO: this doesn't do anything yet.
        # self.selector.update(up)

        # TODO: this doesn't do anything yet.
        # self.cluster_metadata.update(up)

        if add_to_stack:
            self._global_history.action(self.clustering)

        # Refresh the views with the DataUpdate instance.
        for view in self._view_manager.views:
            if isinstance(view, WaveformView):
                self._update_waveforms_after_cluster(view, up=up)
            view.update()

    # Waveforms.
    # -------------------------------------------------------------------------

    def _update_waveforms_after_load(self, view):
        assert isinstance(view, WaveformView)
        view.visual.spike_clusters = self.clustering.spike_clusters
        view.visual.cluster_metadata = self.cluster_metadata
        view.visual.channel_positions = self.model.probe.positions

    def _update_waveforms_after_select(self, view):
        assert isinstance(view, WaveformView)
        spikes = self.selector.selected_spikes
        view.visual.waveforms = self.model.waveforms[spikes]
        view.visual.masks = self.model.masks[spikes]
        view.visual.spike_labels = spikes

    def _update_waveforms_after_cluster(self, view, up=None):
        # TODO
        assert isinstance(view, WaveformView)

    # Public properties.
    # -------------------------------------------------------------------------

    @property
    def cluster_labels(self):
        """Labels of all current clusters."""
        return self.clustering.cluster_labels

    @property
    def cluster_colors(self):
        """Colors of all current clusters."""
        return [self.cluster_metadata[cluster]['color']
                for cluster in self.clustering.cluster_labels]

    # Public view methods.
    # -------------------------------------------------------------------------

    def show_clusters(self):
        """Create and show a new cluster view."""
        from IPython.display import display
        view = ClusterView(clusters=self.cluster_labels,
                           colors=self.cluster_colors)
        view.on_trait_change(lambda _, __, clusters: self.select(clusters),
                             'value')
        load_css('static/widgets.css')
        display(view)

    def show_waveforms(self):
        """Create and show a new Waveform view."""
        view = WaveformView()
        self._view_manager.register(view)
        self._update_waveforms_after_load(view)
        self._update_waveforms_after_select(view)
        return view

    def close_view(self, view):
        self._view_manager.unregister(view)
        view.close()

    # Public clustering actions.
    # -------------------------------------------------------------------------

    def select(self, clusters):
        """Select some clusters."""
        self.selector.selected_clusters = clusters
        self._update_after_select()

    def merge(self, clusters):
        """Merge clusters."""
        up = self.clustering.merge(clusters)
        self._update_after_cluster(up)

    def split(self, spikes):
        """Create a new cluster from a selection of spikes."""
        up = self.clustering.split(spikes)
        self._update_after_cluster(up)

    def move(self, clusters, group):
        """Move clusters to a group."""
        self.cluster_metadata.set(clusters, 'group', group)
        self._global_history.action(self.cluster_metadata)

    def undo(self):
        """Undo the last action."""
        up = self._global_history.undo()
        self._update_after_cluster(up, add_to_stack=False)

    def redo(self):
        """Redo the last undone action."""
        up = self._global_history.redo()
        self._update_after_cluster(up, add_to_stack=False)

    def wizard_start(self):
        raise NotImplementedError()

    def wizard_next(self):
        raise NotImplementedError()

    def wizard_previous(self):
        raise NotImplementedError()

    def wizard_reset(self):
        raise NotImplementedError()