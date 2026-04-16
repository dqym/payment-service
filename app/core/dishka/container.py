from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider

from app.core.dishka.providers import AppProvider


def create_async_container():
    return make_async_container(AppProvider(), FastapiProvider())
