"""New party chats (Y button / the party chat icon). Add yours here; docs/re-party-chat.md explains.

Each Chat says where it plays (a place from dsde.party_chat_places, or ANYWHERE), when (story flags:
on = all set, off = none set, any_on, not_all_on), the talk (one Say per text box), and the hint, shown
last. A Say is (who, text, face): who is Jian, Lucia, Gabryel, Flora, or Rufus; text is up to 5 lines
of up to 30 characters, split with \\n; {Place names} show blue and [items] in the item color; face is
the expression, 0 to 3.

A chat may ask a YES/NO question after its talk (choice=Choice(ask, yes=Answer(flag, talk),
no=Answer(flag, talk))): A or YES plays the yes side, B or NO the no side. Each side sets its own flag
(0x244..0x25F, feat_party_chat.CHOICE_FLAGS) and clears the other's, so later chats (when=Flags(on=...))
and map scripts can test what Jian said. The buttons only read YES and NO: the question names the choice,
in up to 4 lines. Both sides then go on to the hint.

These are checked before the vanilla hints (party_chat_hints.py), in this order: the first unread chat
that matches plays (and the icon bounces until it has), then the next one. A chat with chain=HINT also
replaces the vanilla hint wherever it matches. Appending keeps the "already read" marks in saves;
inserting in the middle only makes some chats bounce again.
"""

from dsde.party_chat import Answer, Chat, Choice, Flags, Say
from dsde.party_chat_places import ANYWHERE, FOUNTAIN_SQUARE

# EXAMPLE choice flags: what Jian told Lucia about being late (Fountain Square example below)
TOLD_LUCIA_TRUTH = 0x244
DODGED_LUCIA = 0x245

CHATS: tuple[Chat, ...] = (
    # EXAMPLE, to replace: a two-way chat with a choice in Fountain Square once Jian has met Lucia
    # (flag 0xB) and before she has explained the delivery (0x1C).
    Chat(
        where=FOUNTAIN_SQUARE,
        when=Flags(on=(0xB,), off=(0x1C,)),
        talk=(Say("Lucia", "You're late, Jian. Again.", face=3),),
        choice=Choice(
            ask=Say("Jian", "Should I tell her I\noverslept?", face=0),
            yes=Answer(
                TOLD_LUCIA_TRUTH,
                (
                    Say(
                        "Jian",
                        "Okay, okay. I overslept.\nCherenkov had to yell\ntwice.",
                        face=0,
                    ),
                    Say("Lucia", "At least you're honest.\nThat's something.", face=1),
                ),
            ),
            no=Answer(
                DODGED_LUCIA,
                (
                    Say(
                        "Jian",
                        "I was barely late!\nThe square's still here,\nisn't it?",
                        face=0,
                    ),
                    Say("Lucia", "Sure, Jian. Sure.", face=3),
                ),
            ),
        ),
        hint=Say(
            "Lucia",
            "Come on. This package goes to\nGad's Express in\n{Perit Village}.",
            face=1,
        ),
        note="example chat with a choice",
    ),
    # EXAMPLE, to replace: remembers the answer above, at the next stage (0x1C on, before 0x14).
    Chat(
        where=ANYWHERE,
        when=Flags(on=(0x1C, TOLD_LUCIA_TRUTH), off=(0x14,)),
        talk=(
            Say(
                "Lucia",
                "Next time, set two alarms.\nOr I'll come wake you\nmyself.",
                face=1,
            ),
            Say("Jian", "You wouldn't dare.", face=0),
        ),
        hint=Say("Lucia", "Now, Gad's Express.\nIt's in {Perit Village}.", face=1),
        note="example chat that remembers the choice",
    ),
)
