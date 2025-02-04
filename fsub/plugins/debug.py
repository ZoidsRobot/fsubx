import io
import os
import subprocess
from typing import Any

from meval import meval
from pyrogram.filters import command, private, user
from pyrogram.handlers import MessageHandler as Msg
from pyrogram.types import Message

from fsub import Bot


async def log(_: Bot, message: Message):
    await message.reply_document("log.txt", quote=True)


async def evaluate(client: Bot, message: Message):
    if len(message.command) == 1:
        return await message.reply("<pre language='python'>None</pre>", quote=True)

    msg = await message.reply("...", quote=True)

    code = message.text.split(maxsplit=1)[1]
    output = "<b>Output: </b>"
    Bot.log.info(f"Eval-In: {code}")

    evars = {
        "c": client,
        "m": message,
        "r": message.reply_to_message,
        "u": (message.reply_to_message or message).from_user,
    }

    def _print(*args, **kwargs) -> Any:
        print_out = io.StringIO()
        print(*args, file=print_out, **kwargs)
        return print_out.getvalue()

    evars["print"] = _print

    try:
        result = await meval(code, globals(), **evars)
        output += f"<pre language='python'>{result}</pre>"
        Bot.log.info(f"Eval-Out: {result}")
    except Exception as e:
        Bot.log.info(f"Eval-Out: {e}")
        return await msg.edit("<b>Output:\n" f"</b><pre language='python'>{e}</pre>")

    if len(output) > 4096:
        with open("output.txt", "w") as w:
            w.write(str(result))

        await message.reply_document(
            "output.txt", quote=True, reply_to_message_id=message.id
        )
        os.remove("output.txt")
        return await msg.delete()

    await msg.edit(text=output)


async def restart(client: Bot, message: Message):
    msg = await message.reply("Restarting...")
    await client.mdb.inmsg("rmsg", message.chat.id, msg.id)
    await message.delete()
    subprocess.run(["python", "-m", "fsub"])


Bot.hndlr(Msg(log, filters=command(Bot.cmd.log) & private & user(Bot.env.OWNER_ID)))
Bot.hndlr(
    Msg(evaluate, filters=command(Bot.cmd.evaluate) & private & user(Bot.env.OWNER_ID))
)
Bot.hndlr(
    Msg(restart, filters=command(Bot.cmd.restart) & private & user(Bot.env.OWNER_ID))
)
