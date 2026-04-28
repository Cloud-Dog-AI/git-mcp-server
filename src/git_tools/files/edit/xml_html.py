# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from bs4 import BeautifulSoup
from cloud_dog_storage import path_utils
from lxml import etree

from git_tools.files.io import load_host_bytes, load_host_text, store_host_bytes, store_host_text


def edit_xml_xpath(path: str | object, xpath: str, replacement: str) -> int:
    """Update XML nodes selected by XPath and return modified count."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    root = etree.fromstring(load_host_bytes(file_path))
    nodes = root.xpath(xpath)
    for node in nodes:
        node.text = replacement
    store_host_bytes(file_path, etree.tostring(root, pretty_print=True))
    return len(nodes)


def edit_html_css(path: str | object, selector: str, replacement: str) -> int:
    """Update HTML nodes selected by CSS selector and return modified count."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    soup = BeautifulSoup(load_host_text(file_path), "html.parser")
    nodes = soup.select(selector)
    for node in nodes:
        node.string = replacement
    store_host_text(file_path, str(soup))
    return len(nodes)
