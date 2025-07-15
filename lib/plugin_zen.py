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
        self._items = []

        self._url, self._mode, url_args = url_decode()
        self._handle = int(sys.argv[1])
        arg_args, self._kwargs = arg_decode()
        self._args = url_args if url_args else arg_args

        self._cache_to_disc = True
        self._update_listing = False

    def _get_item(self, label=""):
        return xbmcgui.ListItem(label=label, offscreen=True)

    def _register_mode(self, mode, is_folder=False, is_playable=False):
        def register(method):
            def run(*args, **kwargs):
                if is_playable:
                    item = self._get_item()
                    args = (item, *args)
                try:
                    succeeded = False
                    method(*args, **kwargs)
                    succeeded = True
                finally:
                    if is_playable:
                        xbmcplugin.setResolvedUrl(self._handle, succeeded, item)
                    elif is_folder:
                        xbmcplugin.addDirectoryItems(
                            self._handle, self._items, len(self._items)
                        )
                        xbmcplugin.endOfDirectory(
                            self._handle,
                            succeeded,
                            self._update_listing,
                            self._cache_to_disc,
                        )

            run.is_folder = is_folder
            run.is_playable = is_playable
            self._modes[mode] = run
            return run

        return register

    def register_item(self, mode):
        return self._register_mode(mode)

    def register_folder(self, mode):
        return self._register_mode(mode, is_folder=True)

    def register_playable(self, mode):
        return self._register_mode(mode, is_playable=True)

    def add_item_by_url(self, label, url, is_folder=False, is_playable=True):
        item = self._get_item(label)
        if is_playable:
            item.setProperty("isPlayable", "true")
        self._items.append(
            (
                url,
                item,
                is_folder,
            )
        )
        return item

    def add_item_by_mode(self, label, mode, *args, **kwargs):
        return self.add_item_by_url(
            label,
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
