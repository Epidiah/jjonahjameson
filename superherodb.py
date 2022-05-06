from pathlib import Path
import json

"""
Herein we control the data used for JJJ's game of I'm Not Spider-Man, as well as
the logic used while playing the game.
"""


async def ask(communicator, async_input_func, q):
    while True:
        await communicator(q)
        rsp = await async_input_func()
        if (
            rsp.content.lower().startswith("yes")
            or rsp.content.lower().startswith("yup")
            or rsp.content.lower() == "y"
        ):
            return True
        elif rsp.content.lower().startswith("no") or rsp.content.lower() == "n":
            return False
        else:
            await communicator("Come on, YES or NO! This ain't a tough question!\n")


async def new_super(old_super, communicator, async_input_func):
    await communicator("Who are you, then?")
    new_name = await async_input_func()
    new_name = new_name.content
    await communicator(
        f"How am I supposed to keep track of you all?\nIf I were you and you were me, what yes or no question would you ask to tell me apart from {old_super.text}?"
    )
    new_question = await async_input_func()
    print(new_question.content)
    new_question = new_question.content
    ans = await ask(communicator, async_input_func, "And you would answer...?")
    await communicator("That's what I thought! Now, go get me that menace, SPIDER-MAN!")
    if ans:
        return Question(new_question, Answer(new_name), old_super)
    else:
        return Question(new_question, old_super, Answer(new_name))


class Knowledge:
    """
    A base class for the Question and Answer classes.
    """

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(know_dict):
        if "if_yes" in know_dict:
            return Question(**know_dict)
        else:
            return Answer(**know_dict)


class Question(Knowledge):
    """
    Represents a question node in the knowledge base.
    """

    def __init__(self, text, if_yes, if_no):
        self.text, self.if_yes, self.if_no = text, if_yes, if_no
        for k, v in self.__dict__.items():
            if type(v) == dict:
                self.__dict__[k] = self.from_dict(v)

    async def play(self, communicator, async_input_func):
        ans = await ask(communicator, async_input_func, self.text)
        if ans:
            self.if_yes = await self.if_yes.play(communicator, async_input_func)
        else:
            self.if_no = await self.if_no.play(communicator, async_input_func)
        return self

    def __repr__(self):
        return f"Question({self.text}, {self.if_yes}, {self.if_no})"

    def get_answers(self):
        yield from self.if_no.get_answers()
        yield from self.if_yes.get_answers()

    def get_raw_text(self):
        yield self.text
        yield from self.if_no.get_raw_text()
        yield from self.if_yes.get_raw_text()

    def to_dict(self):
        return {
            "text": self.text,
            "if_yes": self.if_yes.to_dict(),
            "if_no": self.if_no.to_dict(),
        }


class Answer(Knowledge):
    """
    Represents an answer node in the knowledge base.
    """

    def __init__(self, text):
        self.text = text

    async def play(self, communicator, async_input_func):
        ans = await ask(communicator, async_input_func, f"Are you {self.text}?")
        if ans:
            if self.text == "SPIDER-MAN":
                await communicator("NO YOU'RE NOT! QUIT WASTING MY TIME, PARKER!")
            else:
                await communicator(
                    "That's what I thought! Now, go get me that menace, SPIDER-MAN!"
                )
            return self
        else:
            return await new_super(self, communicator, async_input_func)

    def __repr__(self):
        return f"Answer({self.text})"

    def get_answers(self):
        yield self.text

    def get_raw_text(self):
        yield self.text


def load_shdb(unique_id, current_dir, verbose=False):
    """
    unique_id: a unique string used to identify the superhero database.
        For Discord, this is useally the guild.id
    current_dir: a Path object for the current directory
    verbose: if True, will print barely useful information to the terminal

    returns: a Knowledge object containing all data from the superhero database
    """
    jpath = Path(current_dir, f"shdb_{unique_id}.json")
    if jpath.is_file():
        if verbose:
            print(f"{datetime.datetime.now()}: Loading shdb_{unique_id}.json...")
        with open(jpath, "r") as json_file:
            shjson = json.load(json_file)
            shdb = Knowledge.from_dict(shjson)
        if verbose:
            print(f"{datetime.datetime.now()}: Loaded shdb_{unique_id}.json.")
    else:
        if verbose:
            print(
                f"{datetime.datetime.now()}: Could not find shdb_{unique_id}.json. Starting from scratch."
            )
        shdb = Question(
            "Do you wear a cape?",
            Question(
                "Is that the Eye of Agamotto around your neck?",
                Answer("Doctor Strange"),
                Answer("Storm"),
            ),
            Answer("SPIDER-MAN"),
        )
    return shdb
