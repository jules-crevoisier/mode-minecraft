"""Texts of the built-in recipe viewer (com.brasshaven.client.recipes: the item list beside inventories, the recipe
screen, the "+" fill button; recipe/RecipeSync and RecipeFill on the server). Merged into the lang files by
gen_assets.py; the GUI mockups (gen_gui.py --mockup) and the validator's screen-fit check read them too."""

# key -> (english, french). %s: the player's keys (R, U), counts, names.
MESSAGES = {
    "key.brasshaven.recipes": ("Recipes of the hovered item", "Recettes de l'objet survolé"),
    "key.brasshaven.uses": ("Uses of the hovered item", "Utilisations de l'objet survolé"),
    "key.brasshaven.recipe_panel": ("Show / hide the item list (recipes)", "Afficher / masquer la liste des objets (recettes)"),
    "gui.brasshaven.recipes.recipes": ("Recipes", "Recettes"),
    "gui.brasshaven.recipes.uses": ("Uses", "Utilisations"),
    "gui.brasshaven.recipes.to_uses": ("Uses: %s", "Utilisations : %s"),
    "gui.brasshaven.recipes.to_recipes": ("Recipes: %s", "Recettes : %s"),
    "gui.brasshaven.recipes.to_uses.tip": ("What this item is used for", "Ce que cet objet sert à fabriquer"),
    "gui.brasshaven.recipes.to_recipes.tip": ("How to make this item", "Comment fabriquer cet objet"),
    "gui.brasshaven.recipes.manual": ("Manual page", "Page du manuel"),
    "gui.brasshaven.recipes.manual.tip": ("This item's page in the Wayfarer's Manual",
                                          "La page de cet objet dans le Manuel du Voyageur"),
    "gui.brasshaven.recipes.manual.none": ("No manual page for this item", "Pas de page du manuel pour cet objet"),
    "gui.brasshaven.recipes.back": ("Back", "Retour"),
    "gui.brasshaven.recipes.back.tip": ("The previous item (Backspace)", "L'objet précédent (Retour arrière)"),
    "gui.brasshaven.recipes.page": ("%s / %s", "%s / %s"),
    "gui.brasshaven.recipes.tab": ("%s - %s", "%s - %s"),
    "gui.brasshaven.recipes.count": ("%s recipe(s)", "%s recette(s)"),
    "gui.brasshaven.recipes.cat.crafting": ("Crafting", "Fabrication"),
    "gui.brasshaven.recipes.cat.smelting": ("Furnace", "Four"),
    "gui.brasshaven.recipes.cat.blasting": ("Blast Furnace", "Haut fourneau"),
    "gui.brasshaven.recipes.cat.smoking": ("Smoker", "Fumoir"),
    "gui.brasshaven.recipes.cat.campfire": ("Campfire", "Feu de camp"),
    "gui.brasshaven.recipes.cat.stonecutting": ("Stonecutter", "Tailleur de pierre"),
    "gui.brasshaven.recipes.cat.smithing": ("Smithing Table", "Table de forgeron"),
    "gui.brasshaven.recipes.cat.chisel": ("Chisel Table", "Table de taille"),
    "gui.brasshaven.recipes.cat.other": ("Other", "Autres"),
    "gui.brasshaven.recipes.waiting": ("The server has not sent its recipes yet.", "Le serveur n'a pas encore envoyé ses recettes."),
    "gui.brasshaven.recipes.no_recipes": ("No known recipe makes %s.", "Aucune recette connue ne fabrique : %s."),
    "gui.brasshaven.recipes.no_uses": ("No known recipe uses %s.", "Aucune recette connue n'utilise : %s."),
    "gui.brasshaven.recipes.cook": ("%s s - %s XP", "%s s - %s XP"),
    "gui.brasshaven.recipes.fill": ("Fill the grid", "Remplir la grille"),
    "gui.brasshaven.recipes.fill.tip": ("Takes the ingredients from your inventory", "Prend les ingrédients dans ton inventaire"),
    "gui.brasshaven.recipes.fill.max": ("Shift + click: as many as possible", "Maj + clic : le plus possible"),
    "gui.brasshaven.recipes.fill.missing": ("Missing:", "Il manque :"),
    "gui.brasshaven.recipes.fill.ghost": ("The grid will show the recipe's outline", "La grille montrera le contour de la recette"),
    "gui.brasshaven.recipes.missing": ("Not in your inventory", "Pas dans ton inventaire"),
    "gui.brasshaven.recipes.alternatives": ("One of %s items (Shift: hold still)", "Un objet parmi %s (Maj : figer)"),
    "gui.brasshaven.recipes.id": ("Recipe %s", "Recette %s"),
    "gui.brasshaven.recipes.shapeless": ("Shapeless: any arrangement in the grid", "Sans forme : n'importe où dans la grille"),
    "gui.brasshaven.recipes.keys": ("%s / click: recipes - %s / right click: uses", "%s / clic : recettes - %s / clic droit : utilisations"),
    "gui.brasshaven.recipes.tooltip": ("%s: recipes - %s: uses", "%s : recettes - %s : utilisations"),
    "gui.brasshaven.recipes.search": ("Search...", "Rechercher..."),
    "gui.brasshaven.recipes.search.tip": ("A name, @mod or #tag. Right click: clear.", "Un nom, @mod ou #tag. Clic droit : effacer."),
    "gui.brasshaven.recipes.nothing": ("Nothing found", "Rien trouvé"),
    "gui.brasshaven.recipes.filter.mod": ("Brasshaven items only", "Objets Brasshaven seulement"),
    "gui.brasshaven.recipes.filter.all": ("Every item (Brasshaven first)", "Tous les objets (Brasshaven d'abord)"),
    "gui.brasshaven.recipes.filter.tip": ("Click to switch", "Clic pour changer"),
    "gui.brasshaven.recipes.list": ("Item list", "Liste des objets"),
    "gui.brasshaven.recipes.list.tip": ("No room beside this window: the list opens full screen.",
                                        "Pas de place à côté de cette fenêtre : la liste s'ouvre en plein écran."),
    "gui.brasshaven.settings.recipe_viewer": ("Recipe viewer", "Livre de recettes"),
    "gui.brasshaven.settings.recipe_viewer.tip": ("R over an item in any inventory: its recipes; U: its uses.",
                                                  "R sur un objet dans un inventaire : ses recettes ; U : ses utilisations."),
    "gui.brasshaven.settings.recipe_panel": ("Item list", "Liste des objets"),
    "gui.brasshaven.settings.recipe_panel.tip": ("The searchable item list beside inventories (I shows / hides it).",
                                                 "La liste des objets avec recherche à côté des inventaires (I l'affiche ou la masque)."),
}


def lang():
    en, fr = {}, {}
    for key, (e, f) in MESSAGES.items():
        en[key], fr[key] = e, f
    return en, fr


def text(key, li, *args):
    s = MESSAGES[key][li]
    return s % args if args else s
