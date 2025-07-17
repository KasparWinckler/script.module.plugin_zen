import base64
import json
import sys
import urllib.parse
import xbmcgui
import xbmcplugin


def arg_decode(arg=sys.argv[2]):
    if arg:
        return json.loads(base64.urlsafe_b64decode(urllib.parse.unquote(arg[1:])))
    else:
        return [], {}


def arg_encode(*args, **kwargs):
    if args or kwargs:
        return "?" + urllib.parse.quote(
            base64.b64encode(json.dumps([args, kwargs]).encode())
        )
    else:
        return ""


def url_decode(url=sys.argv[0]):
    parts = url.split("/")
    return (
        "/".join(parts[0:3]) + "/",
        parts[3] if len(parts) > 3 else "",
        parts[4:0],
    )


class _Plugin:
    def __init__(self):
        self._modes = {}
        self._url, self._mode, url_args = url_decode()
        self._handle = int(sys.argv[1])
        arg_args, self._kwargs = arg_decode()
        self._args = url_args if url_args else arg_args

    def _register_mode(self, mode, is_folder=False, is_playable=False):
        def register(method):
            if is_folder:

                def run(*args, **kwargs):
                    self._items = []
                    self._cache_to_disc = True
                    self._update_listing = False
                    try:
                        succeeded = False
                        method(*args, **kwargs)
                        succeeded = True
                    finally:
                        xbmcplugin.addDirectoryItems(
                            self._handle, self._items, len(self._items)
                        )
                        xbmcplugin.endOfDirectory(
                            self._handle,
                            succeeded,
                            self._update_listing,
                            self._cache_to_disc,
                        )
            else:

                def run(*args, **kwargs):
                    item = xbmcgui.ListItem(offscreen=True)
                    try:
                        succeeded = False
                        method(item, *args, **kwargs)
                        succeeded = True
                    finally:
                        if is_playable:
                            xbmcplugin.setResolvedUrl(self._handle, succeeded, item)

            run.is_folder = is_folder
            run.is_playable = is_playable
            self._modes[mode] = run
            return run

        return register

    def mode_item(self, mode):
        return self._register_mode(mode)

    def mode_folder(self, mode):
        return self._register_mode(mode, is_folder=True)

    def mode_playable(self, mode):
        return self._register_mode(mode, is_playable=True)

    def add_item_for_path(self, path, is_folder=False, is_playable=False):
        item = xbmcgui.ListItem(offscreen=True)
        if is_playable:
            item.setProperty("isPlayable", "true")
        self._items.append(
            (
                path,
                item,
                is_folder,
            )
        )
        return item

    def add_item(self, mode, *args, **kwargs):
        return self.add_item_for_path(
            self._url + mode + arg_encode(*args, **kwargs),
            self._modes[mode].is_folder,
            self._modes[mode].is_playable,
        )

    def set_update_listing(self, b):
        self._update_listing = b

    def set_cache_to_disc(self, b):
        self._cache_to_disc = b

    def run(self):
        self._modes[self._mode](*self._args, **self._kwargs)

    def xbmcplugin(self, name, *args, **kwargs):
        attr = getattr(xbmcplugin, name)
        if callable(attr):
            return attr(self._handle, *args, **kwargs)
        else:
            return attr


PLUGIN = _Plugin()
