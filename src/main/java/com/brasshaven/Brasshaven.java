package com.brasshaven;

import com.mojang.logging.LogUtils;
import com.brasshaven.command.BrasshavenCommand;
import com.brasshaven.config.BrasshavenConfig;
import com.brasshaven.event.CoopEvents;
import com.brasshaven.event.DangerEvents;
import com.brasshaven.event.EquipmentEvents;
import com.brasshaven.event.GraveEvents;
import com.brasshaven.generated.BossGear;
import com.brasshaven.generated.ModDecor;
import com.brasshaven.registry.ModBlockEntities;
import com.brasshaven.registry.ModBlocks;
import com.brasshaven.registry.ModDataComponents;
import com.brasshaven.registry.ModEntities;
import com.brasshaven.registry.ModItems;
import com.brasshaven.registry.ModTabs;
import net.minecraft.resources.Identifier;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.AddPackFindersEvent;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.eventbus.api.bus.BusGroup;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.fml.loading.FMLEnvironment;
import org.slf4j.Logger;

/**
 * Brasshaven: an exploration-first co-op survival mod.
 *
 * <p>Content is split by concern: {@code registry} declares every block/item/entity,
 * {@code event} holds the gameplay hooks (shared quests, graves, set bonuses, area tools),
 * {@code command} exposes the {@code /brasshaven} command that clickable chat menus and
 * key bindings rely on, and {@code client} is only ever loaded on the physical client.
 */
@Mod(Brasshaven.MODID)
public final class Brasshaven {
    public static final String MODID = "brasshaven";
    public static final Logger LOGGER = LogUtils.getLogger();

    public Brasshaven(FMLJavaModLoadingContext context) {
        BusGroup modBus = context.getModBusGroup();
        ModDecor.init();
        BossGear.init();
        com.brasshaven.generated.GeneratedMetals.init();
        com.brasshaven.generated.GeneratedMachines.init();
        com.brasshaven.generated.GeneratedFurniture.init();
        com.brasshaven.generated.GeneratedWorldBlocks.init();
        com.brasshaven.registry.ModOcean.init();
        com.brasshaven.registry.ModSocial.init();
        com.brasshaven.relic.RelicGear.init(); // relic gear of the colossal structures
        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModBlockEntities.BLOCK_ENTITIES.register(modBus);
        ModEntities.ENTITIES.register(modBus);
        com.brasshaven.registry.ModOcean.FEATURES.register(modBus);
        ModTabs.TABS.register(modBus);
        ModDataComponents.COMPONENTS.register(modBus);
        com.brasshaven.registry.ModMenus.MENUS.register(modBus);
        com.brasshaven.registry.ModWorldgen.POOL_ELEMENTS.register(modBus);
        com.brasshaven.registry.ModWorldgen.PLACEMENTS.register(modBus);
        com.brasshaven.registry.ModWorldgen.STRUCTURE_TYPES.register(modBus);
        com.brasshaven.registry.ModWorldgen.PLACEMENT_MODIFIERS.register(modBus);
        com.brasshaven.registry.ModWorldgen.BIOME_MODIFIERS.register(modBus);
        com.brasshaven.network.BrasshavenNet.init();

        EntityAttributeCreationEvent.BUS.addListener(ModEntities::registerAttributes);
        RegisterCommandsEvent.BUS.addListener(BrasshavenCommand::register);
        AddPackFindersEvent.BUS.addListener(com.brasshaven.world.CustomBiomesPack::addPacks);
        CoopEvents.register();
        GraveEvents.register();
        com.brasshaven.map.MapServer.register();
        EquipmentEvents.register();
        DangerEvents.register();
        com.brasshaven.event.QolEvents.register();
        com.brasshaven.event.GadgetEvents.register();
        com.brasshaven.accessory.AccessoryEvents.register();
        com.brasshaven.relic.RelicEvents.register();
        com.brasshaven.event.OceanEvents.register();
        com.brasshaven.skill.SkillEvents.register();
        com.brasshaven.boss.BossDifficulty.register();
        com.brasshaven.util.NpcQuests.register();
        com.brasshaven.chisel.ChiselFamilies.register();
        com.brasshaven.recipe.RecipeSync.register();
        com.brasshaven.util.StructureLocator.register();
        com.brasshaven.world.SiteFit.register();
        com.brasshaven.block.MachineBlockEntity.registerEvents();
        // releases and updates: version check at login, renamed-id remapping, saved-data formats, update notice
        com.brasshaven.release.VersionGate.register();
        com.brasshaven.release.RegistryRemap.register();
        com.brasshaven.data.DataVersions.register();
        com.brasshaven.release.UpdateChecker.register();
        com.brasshaven.util.ServerGuard.register();
        com.brasshaven.util.SpawnCaps.register();
        com.brasshaven.social.Social.register();
        SpawnPlacementRegisterEvent.BUS.addListener(ModEntities::registerSpawnPlacements);
        context.registerConfig(ModConfig.Type.COMMON, BrasshavenConfig.SPEC);
        context.registerConfig(ModConfig.Type.CLIENT, com.brasshaven.config.BrasshavenClientConfig.SPEC);

        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.brasshaven.client.BrasshavenClient.init(modBus, context);
            com.brasshaven.client.social.ClientSocial.init(modBus);
        }
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
