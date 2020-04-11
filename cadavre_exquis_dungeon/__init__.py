#!/usr/bin/env python3

import os
import sys
from time import sleep

import requests # only for exceptions

from ai_dungeon_cli import AiDungeon, Config, TermIo, \
    FailedConfiguration, QuitSession


# -------------------------------------------------------------------------
# UTILS: TERMINAL

class IoPipe():
    def __init__(self):
        self.value = None


class PipedTermIo(TermIo):
    def __init__(self, io_pipe_in: IoPipe, io_pipe_out: IoPipe, prompt: str = ''):
        self.prompt = prompt
        self.io_pipe_in = io_pipe_in
        self.io_pipe_out = io_pipe_out

    def handle_user_input(self) -> str:
        text = self.io_pipe_in.value
        self.handle_basic_output(self.prompt + " " + text)
        return text

    def handle_story_output(self, text: str):
        self.io_pipe_out.value = text



# -------------------------------------------------------------------------
# MAIN

def main():

    try:
        conf = Config.loaded_from_file()

        nb_ia = 2

        io_pipe_list = [IoPipe() for i in range(nb_ia)]

        term_io_list = []
        for i in range(nb_ia):
            pipe_out = io_pipe_list[i]
            j = i + 1
            if j >= nb_ia:
                j = 0
            pipe_out = io_pipe_list[i]
            pipe_in = io_pipe_list[j]
            term_io_list.append(PipedTermIo(pipe_out, pipe_in, str(i + 1) + '> '))

        term_io = term_io_list[0] # for printing exceptions

        ai_list = [AiDungeon(conf, tio) for tio in term_io_list]

        if not ai_list[0].get_auth_token():
            ai_list[0].login()
            auth_token = ai_list[0].conf.auth_token
            for i in range(1, nb_ia):
                ai_list[i].conf.auth_token = auth_token

        for ai in ai_list:
            ai.update_session_auth()

        custom_story = "You are part of an exquisite corpse. Others are like you."
        for ai in ai_list:
            ai.story_configuration = {
                "storyMode": "custom",
                "characterType": None,
                "name": None,
                "customPrompt": custom_story,
                "promptId": None,
            }

        for ai in ai_list:
            ai.init_story()

        i = 0
        while True:
            sleep(5)
            ai_list[i].process_next_action()
            i += 1
            if i >= len(ai_list):
                i = 0


    except FailedConfiguration as e:
        # NB: No UserIo initialized at this level
        # hence we fallback to a classic `print`
        print(e.message)
        exit(1)

    except QuitSession:
        term_io.handle_basic_output("Bye Bye!")

    except KeyboardInterrupt:
        term_io.handle_basic_output("Received Keyboard Interrupt. Bye Bye...")

    except requests.exceptions.TooManyRedirects:
        term_io.handle_basic_output("Exceded max allowed number of HTTP redirects, API backend has probably changed")
        exit(1)

    except requests.exceptions.HTTPError as err:
        term_io.handle_basic_output("Unexpected response from API backend:")
        term_io.handle_basic_output(err)
        exit(1)

    except ConnectionError:
        term_io.handle_basic_output("Lost connection to the Ai Dungeon servers")
        exit(1)

    except requests.exceptions.RequestException as err:
        term_io.handle_basic_output("Totally unexpected exception:")
        term_io.handle_basic_output(err)
        exit(1)


if __name__ == "__main__":
    main()
