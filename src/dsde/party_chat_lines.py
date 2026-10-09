"""New party chats (Y button / the party chat icon). Add yours here; docs/re-party-chat.md explains.

Each Chat says where it plays (a place from dsde.party_chat_places, or ANYWHERE), when (story flags:
on = all set, off = none set, any_on, not_all_on), the talk (one Say per text box), and the hint, shown
last. A Say is (who, text, face): who is Jian, Lucia, Gabryel, Flora, or Rufus; text is up to 5 lines
of up to 30 characters, split with \\n; {Place names} show blue and [items] in the item color; face is
the expression, 0 to 3.

These are checked before the vanilla hints (party_chat_hints.py), in this order: the first unread chat
that matches plays (and the icon bounces until it has), then the next one. A chat with chain=HINT also
replaces the vanilla hint wherever it matches. Appending keeps the "already read" marks in saves;
inserting in the middle only makes some chats bounce again.
"""

from dsde.party_chat import Chat, Flags, Say
from dsde.party_chat_places import FOUNTAIN_SQUARE

CHATS: tuple[Chat, ...] = (
    # EXAMPLE, to replace: a two-way chat in Fountain Square once Jian has met Lucia (flag 0xB) and
    # before she has explained the delivery (0x1C).
    Chat(
        where=FOUNTAIN_SQUARE,
        when=Flags(on=(0xB,), off=(0x1C,)),
        talk=(
            Say("Lucia", "You're late, Jian. Again.", face=3),
            Say(
                "Jian",
                "I was barely late!\nThe square's still here,\nisn't it?",
                face=0,
            ),
        ),
        hint=Say(
            "Lucia",
            "Come on. This package goes to\nGad's Express in\n{Perit Village}.",
            face=1,
        ),
        note="example two-way chat",
    ),
)
