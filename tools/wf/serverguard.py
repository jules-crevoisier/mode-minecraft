"""Messages of the server guards (com.brasshaven.util.ServerGuard and the server options of BrasshavenConfig, see
docs/SERVER_ADMIN.md): refusals a player sees when a server rule stops an action. Merged into the lang files by
gen_assets.py."""

# key -> (english, french)
MESSAGES = {
    "message.brasshaven.machine.chunk_full": ("This chunk already holds %s machines: the server allows no more.",
                                             "Ce chunk contient déjà %s machines : le serveur n'en autorise pas plus."),
    "message.brasshaven.waystone.full": ("The server already knows %s waystones: no new one can be activated.",
                                        "Le serveur connaît déjà %s pierres de voyage : aucune nouvelle ne peut être activée."),
    "message.brasshaven.waystone.rename_here": ("You can only rename or pin the waystone you stand at.",
                                               "Tu ne peux renommer ou épingler que la pierre de voyage où tu te trouves."),
    "message.brasshaven.waystone.no_cross_dimension": ("This server does not allow travel to another dimension by waystone.",
                                                      "Ce serveur n'autorise pas le voyage vers une autre dimension par pierre de voyage."),
    "message.brasshaven.waystone.cooldown": ("The waystones need %s more seconds before your next journey.",
                                            "Les pierres de voyage ont besoin de %s secondes avant ton prochain voyage."),
    "message.brasshaven.waystone.cost": ("This journey costs %s experience levels.",
                                        "Ce voyage coûte %s niveaux d'expérience."),
    "message.brasshaven.grave.locked": ("This grave belongs to %s: only they can open it.",
                                       "Cette tombe appartient à %s : seul ce joueur peut l'ouvrir."),
    "message.brasshaven.grave.locked_for": ("This grave belongs to %s: only they can open it for %s more minutes.",
                                           "Cette tombe appartient à %s : seul ce joueur peut l'ouvrir pendant encore %s minutes."),
    "message.brasshaven.compass.busy": ("The compass is still turning: try again in a few seconds.",
                                       "La boussole tourne encore : réessaie dans quelques secondes."),
}


def lang():
    en, fr = {}, {}
    for key, (e, f) in MESSAGES.items():
        en[key], fr[key] = e, f
    return en, fr
