package com.brasshaven.social;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.brasshaven.Brasshaven;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Everything the multiplayer features keep between restarts, in one file (data/brasshaven_social.dat of the
 * overworld): the names of every player who ever joined (mail goes to offline players), the companies, the
 * Pneumatic Post inboxes, the open contracts with their escrowed rewards, and the duel records.
 *
 * <p>Items held here (parcels, rewards) left a player's inventory in the same server tick that put them here, and
 * leave here in the same tick that puts them back: no item is ever in two places. Lists of items are decoded one
 * stack at a time, so an item removed from the game (an uninstalled mod) costs only that stack, never the file.
 */
public final class SocialData extends SavedData {
    // ------------------------------------------------------------------ records
    public record Member(UUID id, String name) {
        static final Codec<Member> CODEC = RecordCodecBuilder.create(b -> b.group(
                UUIDUtil.CODEC.fieldOf("id").forGetter(Member::id),
                Codec.STRING.fieldOf("name").forGetter(Member::name)
        ).apply(b, Member::new));
    }

    /** A company: a named group of players with a leader and two switches. */
    public static final class Company {
        static final Codec<Company> CODEC = RecordCodecBuilder.create(b -> b.group(
                Codec.INT.fieldOf("id").forGetter(c -> c.id),
                Codec.STRING.fieldOf("name").forGetter(c -> c.name),
                UUIDUtil.CODEC.fieldOf("leader").forGetter(c -> c.leader),
                Member.CODEC.listOf().fieldOf("members").forGetter(c -> List.copyOf(c.members.values())),
                Codec.BOOL.optionalFieldOf("friendly_fire", false).forGetter(c -> c.friendlyFire),
                Codec.BOOL.optionalFieldOf("share_xp", false).forGetter(c -> c.shareXp)
        ).apply(b, Company::new));

        public final int id;
        public String name;
        public UUID leader;
        /** In joining order. */
        public final LinkedHashMap<UUID, Member> members = new LinkedHashMap<>();
        public boolean friendlyFire;
        public boolean shareXp;

        Company(int id, String name, UUID leader, List<Member> members, boolean friendlyFire, boolean shareXp) {
            this.id = id;
            this.name = name;
            this.leader = leader;
            members.forEach(m -> this.members.put(m.id(), m));
            this.friendlyFire = friendlyFire;
            this.shareXp = shareXp;
        }
    }

    /**
     * One letter or parcel in an inbox. {@code kind}: "letter" (written by a player), or a system parcel:
     * "delivery" (goods of a fulfilled contract, text = who delivered), "reward" (a contract reward that did not fit the
     * deliverer's bag), "refund" (reward of a cancelled or expired contract), "returned" (items given back because a
     * screen was closed while offline or dead).
     */
    public record Parcel(long id, UUID from, String fromName, String text, List<ItemStack> items, long sentAt, String kind) {
        static final Codec<Parcel> CODEC = RecordCodecBuilder.create(b -> b.group(
                Codec.LONG.fieldOf("id").forGetter(Parcel::id),
                UUIDUtil.CODEC.fieldOf("from").forGetter(Parcel::from),
                Codec.STRING.fieldOf("from_name").forGetter(Parcel::fromName),
                Codec.STRING.optionalFieldOf("text", "").forGetter(Parcel::text),
                SocialCodecs.ITEMS.optionalFieldOf("items", List.of()).forGetter(Parcel::items),
                Codec.LONG.fieldOf("sent").forGetter(Parcel::sentAt),
                Codec.STRING.optionalFieldOf("kind", "letter").forGetter(Parcel::kind)
        ).apply(b, Parcel::new));

        public boolean system() {
            return !kind.equals("letter");
        }
    }

    /** An open contract: "bring {amount} x {wanted}", paid with the escrowed {@code reward}. */
    public static final class Contract {
        static final Codec<Contract> CODEC = RecordCodecBuilder.create(b -> b.group(
                Codec.LONG.fieldOf("id").forGetter(c -> c.id),
                UUIDUtil.CODEC.fieldOf("poster").forGetter(c -> c.poster),
                Codec.STRING.fieldOf("poster_name").forGetter(c -> c.posterName),
                ItemStack.CODEC.fieldOf("wanted").forGetter(c -> c.wanted),
                Codec.INT.fieldOf("amount").forGetter(c -> c.amount),
                Codec.STRING.optionalFieldOf("note", "").forGetter(c -> c.note),
                SocialCodecs.ITEMS.fieldOf("reward").forGetter(c -> c.reward),
                Codec.LONG.fieldOf("posted").forGetter(c -> c.postedAt),
                Codec.LONG.fieldOf("expires").forGetter(c -> c.expiresAt)
        ).apply(b, Contract::new));

        public final long id;
        public final UUID poster;
        public final String posterName;
        /** One item (count 1): the exact item wanted, components included. */
        public final ItemStack wanted;
        public final int amount;
        public final String note;
        public final List<ItemStack> reward;
        public final long postedAt;
        public final long expiresAt;

        Contract(long id, UUID poster, String posterName, ItemStack wanted, int amount, String note, List<ItemStack> reward,
                 long postedAt, long expiresAt) {
            this.id = id;
            this.poster = poster;
            this.posterName = posterName;
            this.wanted = wanted.copyWithCount(1);
            this.amount = amount;
            this.note = note;
            this.reward = new ArrayList<>(reward);
            this.postedAt = postedAt;
            this.expiresAt = expiresAt;
        }
    }

    /** Duel results of one player. */
    public record DuelRecord(int wins, int losses, int draws) {
        static final Codec<DuelRecord> CODEC = RecordCodecBuilder.create(b -> b.group(
                Codec.INT.fieldOf("wins").forGetter(DuelRecord::wins),
                Codec.INT.fieldOf("losses").forGetter(DuelRecord::losses),
                Codec.INT.optionalFieldOf("draws", 0).forGetter(DuelRecord::draws)
        ).apply(b, DuelRecord::new));

        public static final DuelRecord NONE = new DuelRecord(0, 0, 0);
    }

    public static final Codec<SocialData> CODEC = RecordCodecBuilder.create(b -> b.group(
            Codec.unboundedMap(UUIDUtil.STRING_CODEC, Codec.STRING).optionalFieldOf("names", Map.of()).forGetter(d -> d.names),
            SocialCodecs.lenientList(Company.CODEC, "company").optionalFieldOf("companies", List.of()).forGetter(d -> List.copyOf(d.companies.values())),
            Codec.unboundedMap(UUIDUtil.STRING_CODEC, SocialCodecs.lenientList(Parcel.CODEC, "parcel")).optionalFieldOf("inboxes", Map.of())
                    .forGetter(d -> d.inboxes),
            SocialCodecs.lenientList(Contract.CODEC, "contract").optionalFieldOf("contracts", List.of()).forGetter(d -> List.copyOf(d.contracts.values())),
            Codec.unboundedMap(UUIDUtil.STRING_CODEC, DuelRecord.CODEC).optionalFieldOf("duels", Map.of()).forGetter(d -> d.duels),
            Codec.LONG.optionalFieldOf("next_id", 1L).forGetter(d -> d.nextId)
    ).apply(b, SocialData::new));

    public static final SavedDataType<SocialData> TYPE = new SavedDataType<>(
            Brasshaven.id("social"), SocialData::new, CODEC, null);

    private final Map<UUID, String> names;
    private final Map<Integer, Company> companies = new LinkedHashMap<>();
    private final Map<UUID, List<Parcel>> inboxes = new HashMap<>();
    private final Map<Long, Contract> contracts = new LinkedHashMap<>();
    private final Map<UUID, DuelRecord> duels;
    private long nextId;

    public SocialData() {
        this(Map.of(), List.of(), Map.of(), List.of(), Map.of(), 1L);
    }

    private SocialData(Map<UUID, String> names, List<Company> companies, Map<UUID, List<Parcel>> inboxes,
                       List<Contract> contracts, Map<UUID, DuelRecord> duels, long nextId) {
        this.names = new HashMap<>(names);
        companies.forEach(c -> this.companies.put(c.id, c));
        inboxes.forEach((k, v) -> this.inboxes.put(k, new ArrayList<>(v)));
        contracts.forEach(c -> this.contracts.put(c.id, c));
        this.duels = new HashMap<>(duels);
        this.nextId = nextId;
    }

    public static SocialData get(MinecraftServer server) {
        return server.getLevel(Level.OVERWORLD).getDataStorage().computeIfAbsent(TYPE);
    }

    public long nextId() {
        setDirty();
        return nextId++;
    }

    public void changed() {
        setDirty();
    }

    // ------------------------------------------------------------------ names
    public void rememberName(UUID id, String name) {
        if (!name.equals(names.put(id, name))) {
            setDirty();
        }
    }

    public String name(UUID id) {
        return names.getOrDefault(id, "?");
    }

    /** The player who ever joined under this name (case-insensitive), or null. */
    public UUID byName(String name) {
        for (Map.Entry<UUID, String> e : names.entrySet()) {
            if (e.getValue().equalsIgnoreCase(name)) {
                return e.getKey();
            }
        }
        return null;
    }

    public Collection<String> knownNames() {
        return names.values();
    }

    // ------------------------------------------------------------------ companies
    public Collection<Company> companies() {
        return companies.values();
    }

    public Company company(int id) {
        return companies.get(id);
    }

    public Company companyOf(UUID player) {
        for (Company c : companies.values()) {
            if (c.members.containsKey(player)) {
                return c;
            }
        }
        return null;
    }

    public Company newCompany(String name, UUID leader, String leaderName) {
        int id = (int) nextId();
        Company c = new Company(id, name, leader, List.of(new Member(leader, leaderName)), false, false);
        companies.put(id, c);
        setDirty();
        return c;
    }

    public void removeCompany(int id) {
        if (companies.remove(id) != null) {
            setDirty();
        }
    }

    // ------------------------------------------------------------------ post
    public List<Parcel> inbox(UUID player) {
        return inboxes.getOrDefault(player, List.of());
    }

    public void deliver(UUID to, Parcel parcel) {
        inboxes.computeIfAbsent(to, k -> new ArrayList<>()).add(parcel);
        setDirty();
    }

    public Parcel parcel(UUID owner, long id) {
        for (Parcel p : inbox(owner)) {
            if (p.id() == id) {
                return p;
            }
        }
        return null;
    }

    /** Replaces (or, with null, removes) a parcel of this inbox. */
    public void updateParcel(UUID owner, long id, Parcel replacement) {
        List<Parcel> list = inboxes.get(owner);
        if (list == null) {
            return;
        }
        for (int i = 0; i < list.size(); i++) {
            if (list.get(i).id() == id) {
                if (replacement == null) {
                    list.remove(i);
                } else {
                    list.set(i, replacement);
                }
                break;
            }
        }
        if (list.isEmpty()) {
            inboxes.remove(owner);
        }
        setDirty();
    }

    // ------------------------------------------------------------------ contracts
    public Collection<Contract> contracts() {
        return contracts.values();
    }

    public Contract contract(long id) {
        return contracts.get(id);
    }

    public void addContract(Contract c) {
        contracts.put(c.id, c);
        setDirty();
    }

    /** Takes the contract off the board; the caller owns its reward from then on. */
    public Contract removeContract(long id) {
        Contract c = contracts.remove(id);
        if (c != null) {
            setDirty();
        }
        return c;
    }

    public Contract newContract(UUID poster, String posterName, ItemStack wanted, int amount, String note, List<ItemStack> reward,
                                long now, long expires) {
        return new Contract(nextId(), poster, posterName, wanted, amount, note, reward, now, expires);
    }

    // ------------------------------------------------------------------ duels
    public DuelRecord duelRecord(UUID player) {
        return duels.getOrDefault(player, DuelRecord.NONE);
    }

    public void recordDuel(UUID player, int win, int loss, int draw) {
        DuelRecord r = duelRecord(player);
        duels.put(player, new DuelRecord(r.wins() + win, r.losses() + loss, r.draws() + draw));
        setDirty();
    }
}
