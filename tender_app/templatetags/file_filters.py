from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Return the base name of a file path"""
    return os.path.basename(value)

@register.filter
def file_extension(value):
    """Return the file extension"""
    return os.path.splitext(value)[1][1:].upper()

@register.filter
def filesizeformat(bytes):
    """Format file size in human readable format"""
    try:
        bytes = float(bytes)
        kb = bytes / 1024
        if kb >= 1024:
            mb = kb / 1024
            if mb >= 1024:
                gb = mb / 1024
                return f"{gb:.1f} GB"
            return f"{mb:.1f} MB"
        return f"{kb:.1f} KB"
    except (ValueError, TypeError):
        return "0 bytes"
