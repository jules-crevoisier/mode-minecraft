package com.wayfarers;

import com.mojang.logging.LogUtils;
import com.wayfarers.command.WayfarersCommand;
import com.wayfarers.config.WayfarersConfig;
import com.wayfarers.event.CoopEvents;
import com.wayfarers.event.DangerEvents;
import com.wayfarers.event.EquipmentEvents;
import com.wayfarers.event.GraveEvents;
import com.wayfarers.generated.BossGear;
import com.wayfarers.generated.ModDecor;
import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.registry.ModBlocks;
import com.wayfarers.registry.ModDataComponents;
import com.wayfarers.registry.ModEntities;
import com.wayfarers.registry.ModItems;
import com.wayfarers.registry.ModTabs;
import com.wayfarers.world.WorldOverhaul;
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
 * Wayfarers: an exploration-first co-op survival mod.
 *
 * <p>Content is split by concern: {@code registry} declares every block/item/entity,
 * {@code event} holds the gameplay hooks (shared quests, graves, set bonuses, area tools),
 * {@code command} exposes the {@code /wayfarers} command that clickable chat menus and
 * key bindings rely on, and {@code client} is only ever loaded on the physical client.
 */
@Mod(Wayfarers.MODID)
public final class Wayfarers {
    public static final String MODID = "wayfarers";
    public static final Logger LOGGER = LogUtils.getLogger();

    public Wayfarers(FMLJavaModLoadingContext context) {
        BusGroup modBus = context.getModBusGroup();
        ModDecor.init();
        BossGear.init();
        com.wayfarers.generated.GeneratedMetals.init();
        com.wayfarers.generated.GeneratedMachines.init();
        com.wayfarers.generated.GeneratedFurniture.init();
        com.wayfarers.generated.GeneratedWorldBlocks.init();
        com.wayfarers.registry.ModOcean.init();
        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModBlockEntities.BLOCK_ENTITIES.register(modBus);
        ModEntities.ENTITIES.register(modBus);
        com.wayfarers.registry.ModOcean.FEATURES.register(modBus);
        ModTabs.TABS.register(modBus);
        ModDataComponents.COMPONENTS.register(modBus);
        com.wayfarers.registry.ModMenus.MENUS.register(modBus);
        com.wayfarers.registry.ModWorldgen.POOL_ELEMENTS.register(modBus);
        com.wayfarers.registry.ModWorldgen.PLACEMENTS.register(modBus);
        com.wayfarers.registry.ModWorldgen.STRUCTURE_TYPES.register(modBus);
        com.wayfarers.registry.ModWorldgen.DENSITY_FUNCTION_TYPES.register(modBus);
        com.wayfarers.network.WayfarersNet.init();

        EntityAttributeCreationEvent.BUS.addListener(ModEntities::registerAttributes);
        RegisterCommandsEvent.BUS.addListener(WayfarersCommand::register);
        AddPackFindersEvent.BUS.addListener(WorldOverhaul::addPacks);
        CoopEvents.register();
        GraveEvents.register();
        com.wayfarers.map.MapServer.register();
        EquipmentEvents.register();
        DangerEvents.register();
        com.wayfarers.event.QolEvents.register();
        com.wayfarers.event.GadgetEvents.register();
        com.wayfarers.event.OceanEvents.register();
        com.wayfarers.skill.SkillEvents.register();
        com.wayfarers.chisel.ChiselFamilies.register();
        com.wayfarers.util.StructureLocator.register();
        com.wayfarers.world.SiteFit.register();
        com.wayfarers.block.MachineBlockEntity.registerEvents();
        SpawnPlacementRegisterEvent.BUS.addListener(ModEntities::registerSpawnPlacements);
        context.registerConfig(ModConfig.Type.COMMON, WayfarersConfig.SPEC);
        context.registerConfig(ModConfig.Type.CLIENT, com.wayfarers.config.WayfarersClientConfig.SPEC);

        if (FMLEnvironment.dist == Dist.CLIENT) {
            com.wayfarers.client.WayfarersClient.init(modBus, context);
        }
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
