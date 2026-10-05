package com.brasshaven.social;

import com.mojang.datafixers.util.Pair;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.DynamicOps;
import com.mojang.serialization.ListBuilder;
import net.minecraft.world.item.ItemStack;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.List;

/** Codecs of {@link SocialData} (their own class: the records' codecs use them while SocialData initialises). */
final class SocialCodecs {
    private static final Logger LOGGER = LogUtils.getLogger();

    private SocialCodecs() {}

    /** A list decoded element by element: a broken element is logged and skipped instead of failing the whole list. */
    static <E> Codec<List<E>> lenientList(Codec<E> element, String what) {
        return new Codec<>() {
            @Override
            public <T> DataResult<Pair<List<E>, T>> decode(DynamicOps<T> ops, T input) {
                return ops.getList(input).map(stream -> {
                    List<E> out = new ArrayList<>();
                    stream.accept(t -> element.parse(ops, t)
                            .resultOrPartial(e -> LOGGER.warn("Brasshaven social data: skipped a broken {}: {}", what, e))
                            .ifPresent(out::add));
                    return Pair.of(out, input);
                });
            }

            @Override
            public <T> DataResult<T> encode(List<E> list, DynamicOps<T> ops, T prefix) {
                ListBuilder<T> builder = ops.listBuilder();
                for (E e : list) {
                    builder.add(element.encodeStart(ops, e));
                }
                return builder.build(prefix);
            }
        };
    }

    /** Non-empty item stacks. */
    static final Codec<List<ItemStack>> ITEMS = lenientList(ItemStack.CODEC, "item stack");
}
