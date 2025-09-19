const std = @import("std");

const MAX_MSG_LEN: comptime_int = 64;

pub const Message = extern struct {
    content: [MAX_MSG_LEN]u8 = [_]u8{0} ** MAX_MSG_LEN,
    size: usize = 0,

    const Self = @This();

    pub fn update(self: *Self, msg: []const u8) !void {
        if (msg.len > MAX_MSG_LEN) {
            return error.MessageTooLarge;
        }
        for (0..MAX_MSG_LEN) |i| {
            self.content[i] = if (i < msg.len) msg[i] else 0;
        }
        self.size = msg.len;
    }

    pub fn read(self: Self) []const u8 {
        return self.content[0..self.size];
    }
}; 

pub const FullEnvelope = extern struct {
    message: Message = .{},

    const Self = @This();

    pub fn init(self: *Self, msg: []const u8) !void {
        try self.message.update(msg);
    }
};

pub const EmptyEnvelope = extern struct {
    next: ?*Envelope = null,
    prev: ?*Envelope = null,

    const Self = @This();

    pub fn snip_out(self: *Self) void {
        if (self.prev) |prev_env| {
            prev_env.empty.next = self.next;
        }
        if (self.next) |next_env| {
            next_env.empty.prev = self.prev;
        }
    }

    pub fn snap_in(self: *Self, after: ?*Envelope) !void {
        self.prev = after;
        const self_env: *Envelope = @fieldParentPtr("empty", self);
        if (after) |after_env| {
            if (self_env == after_env) {
                return error.EnvelopeLoopDetected;
            }

            self.next = after_env.empty.next;
            if (after_env.empty.next) |next_env| {
                if (self_env == next_env) {
                    return error.EnvelopeLoopDetected;
                }
                next_env.empty.prev = self_env;
            }
            after_env.empty.next = self_env;
        } else {
            self.next = null;
        }
    }
};

pub const Envelope = extern union {
    full: FullEnvelope,
    empty: EmptyEnvelope,
};

const NUM_ENVELOPES: comptime_int = 20;

pub const Enveloper = struct {
    envelopes: [NUM_ENVELOPES]Envelope = [_]Envelope{ .{ .empty = .{} } } ** NUM_ENVELOPES,
    next_empty: ?*Envelope = null,

    const Self = @This();

    fn _link_emptys(self: *Self) void {
        var prev: ?*Envelope = null;

        for (0..self.envelopes.len) |i| {
            self.envelopes[i].empty.prev = prev;
            if (prev) |env| {
                env.empty.next = &self.envelopes[i];
            }

            prev = &self.envelopes[i];
        }
    }

    pub fn init(self: *Self) void {
        self.next_empty = &self.envelopes[0];
        self._link_emptys();
    }

    fn get_empty(self: *Self) ?*Envelope {
        const cur_empty = self.next_empty;

        if (cur_empty) |env| {
            if (env.empty.prev) |prev_env| {
                self.next_empty = prev_env;
            } else {
                self.next_empty = env.empty.next;
            }
            env.empty.snip_out();
        }

        return cur_empty;
    }

    pub fn fill(self: *Self, msg: []const u8) !*FullEnvelope {
        const new_env: *Envelope = self.get_empty() orelse return error.OutOfEnvelopes;
        
        try new_env.full.init(msg);
        return @ptrCast(new_env);
    }

    pub fn recycle(self: *Self, envelope: *Envelope) !void {
        try envelope.empty.snap_in(self.next_empty);
        self.next_empty = envelope;
    }
};

const NUM_MAILBOXES: comptime_int = 10;

pub const Challenge = struct {
    enveloper: Enveloper = .{},
    mailboxes: [NUM_MAILBOXES]?*FullEnvelope = [_]?*FullEnvelope{null} ** NUM_MAILBOXES,
    is_sealed: [NUM_MAILBOXES]bool = [_]bool{false} ** NUM_MAILBOXES,
    secret_envelope: ?*FullEnvelope = null,
    flag: []const u8,

    const Self = @This();

    pub fn init(self: *Self) void {
        self.enveloper.init();
    }

    fn valid_mailbox(self: *Self, mailbox: usize) !void {
        if (mailbox >= self.mailboxes.len) {
            return error.BadMailbox;
        }
    }

    pub fn stuff_mailbox(self: *Self, message: []const u8, mailbox: usize) !void {
        try self.valid_mailbox(mailbox);

        if (self.mailboxes[mailbox]) |_| {
            return error.MailboxInUse;
        } else {
            self.mailboxes[mailbox] = try self.enveloper.fill(message);
        }
    }

    pub fn seal_mailbox(self: *Self, mailbox: usize) !void {
        try self.valid_mailbox(mailbox);
        if (self.mailboxes[mailbox]) |full_env| {
            self.is_sealed[mailbox] = true;
            try self.enveloper.recycle(@fieldParentPtr("full", full_env));
        } else {
            return error.MailboxEmpty;
        }
    }

    pub fn stuff_secret_mailbox(self: *Self) !void {
        if (self.secret_envelope) |_| {
            return error.SecretEnvelopeAlreadyStuffed;
        }

        self.secret_envelope = try self.enveloper.fill(self.flag);
    }

    pub fn open_mailbox(self: *Self, mailbox: usize) ![]const u8 {
        try self.valid_mailbox(mailbox);

        if (self.is_sealed[mailbox]) {
            return error.MailboxSealed;
        }

        if (self.mailboxes[mailbox]) |box| {
            return box.message.content[0..box.message.size];
        }
        return error.MailboxEmpty;
    }
};

const stdout = std.io.getStdOut().writer();
const stdin = std.io.getStdIn().reader();

const MenuOption = enum {
    StuffMailbox,
    OpenMailbox,
    SealMailbox,
    StuffSecretMailbox,
    Exit,

    pub fn parse(option: []const u8) !MenuOption {
        const opt_overflow = @subWithOverflow(try std.fmt.parseInt(u8, option, 10), 1);
        if (opt_overflow[1] == 1) {
            return error.InvalidMenuOption;
        }
        const opt = opt_overflow[0];
        return try std.meta.intToEnum(MenuOption, opt);
    }

    pub fn fmt(comptime self: MenuOption) []const u8 {
        comptime {
            const tag: []const u8 = @tagName(self);
            var n: usize = 0;
            for (0.., tag) |i, c| {
                if (i != 0 and std.ascii.isUpper(c)) {
                    n += 1;
                }
            }
            const pretty_len: usize = n + tag.len;
            var pretty: [pretty_len]u8 = [_]u8{0} ** pretty_len;
            var pretty_idx: usize = 0;
            for (tag, 0..) |tag_c, i| {
                defer pretty_idx += 1;
                pretty[pretty_idx] = tag_c;
                if (i + 1 < tag.len and std.ascii.isUpper(tag[i + 1])) {
                    pretty_idx += 1;
                    pretty[pretty_idx] = ' ';
                }
            }
            const pretty_final = pretty;
            return &pretty_final;
        }
    }
};

pub fn menu() !MenuOption {
    try stdout.print("\nOptions:\n", .{});
    inline for (1.., @typeInfo(MenuOption).@"enum".fields) |i, field| {
        const cur_option: MenuOption = @field(MenuOption, field.name);
        const fmt = comptime .{i, cur_option.fmt()};
        try stdout.print("{}. {s}\n", fmt);
    }

    try stdout.print("\n> ", .{});

    var buf: [10]u8 = [_]u8{0} ** 10;
    const result = try stdin.readUntilDelimiterOrEof(&buf, '\n') orelse return error.InvalidMenuInput;
    return try MenuOption.parse(result);
}

pub fn get_mailbox_number() !usize {
    var mailbox_num: ?usize = null;
    var buf: [10]u8 = [_]u8{0} ** 10;
    while (mailbox_num == null) {
        try stdout.print("Mailbox (0-{})> ", .{NUM_MAILBOXES - 1});
        const input: ?[]u8 = stdin.readUntilDelimiterOrEof(&buf, '\n') catch null;
        if (input) |input_read| {
            mailbox_num = std.fmt.parseInt(usize, input_read, 10) catch null;
        }

        if (mailbox_num) |num| {
            if (num >= NUM_MAILBOXES) {
                try stdout.print("Invalid mailbox: {}\n\n", .{num});
                mailbox_num = null;
            }
        } else {
            try stdout.print("Invalid Input\n\n", .{});
        }
    }
    return mailbox_num.?;
}

pub fn get_message(buf: []u8) ![]const u8 {
    try stdout.print("message (max {} chars)> ", .{MAX_MSG_LEN});
    return (try stdin.readUntilDelimiterOrEof(buf, '\n')).?;
}

pub fn read_flag(buf: []u8) ![]const u8 {
    const flag_file = (try std.fs.openFileAbsolute("/flag", .{})).reader();
    return (try flag_file.readUntilDelimiterOrEof(buf, '\n')).?;
}

pub fn main() !void {
    const test_flag = "pwn.college{testing}";
    var flag_buf: [100]u8 = [_]u8{0} ** 100;
    const flag = read_flag(&flag_buf) catch blk: {
        try stdout.print("Warning: could not open /flag. Using test flag!\n", .{});
        break :blk test_flag;
    };
    var chall: Challenge = .{ .flag = flag};
    chall.init();

    try stdout.print("DSU Mailroom Manager 1.1\n", .{});
    try stdout.print("\"Turning envelopes into heaps of fun!\"\n", .{});
    
    var option: ?MenuOption = null;
    while (option == null or option.? != .Exit) {
        option = menu() catch null;
        if (option) |chosen_option| {
            switch (chosen_option) {
                .StuffMailbox => {
                    var buf: [100]u8 = [_]u8{0} ** 100;
                    const mailbox_num = try get_mailbox_number();
                    const message = try get_message(&buf);
                    if (chall.stuff_mailbox(message, mailbox_num)) {
                        try stdout.print("Mailbox {} stuffed successfully!\n", .{mailbox_num});
                    } else |err| {
                        switch (err) {
                            error.MailboxInUse => {
                                try stdout.print("Error: Mailbox {} is in use!\n", .{mailbox_num});
                            },
                            error.BadMailbox => {
                                try stdout.print("Error: Mailbox {} is invalid!\n", .{mailbox_num});
                            },
                            else => {
                                return err;
                            },
                        }
                    }
                },
                .OpenMailbox => {
                    const mailbox_num = try get_mailbox_number();
                    if (chall.open_mailbox(mailbox_num)) |message| {
                        try stdout.print("Message: {s}\n", .{message});
                    } else |err| {
                        switch (err) {
                            error.MailboxEmpty => {
                                try stdout.print("Error: Mailbox {} is empty!\n", .{mailbox_num});
                            },
                            error.BadMailbox => {
                                try stdout.print("Error: Mailbox {} is invalid!\n", .{mailbox_num});
                            },
                            error.MailboxSealed => {
                                try stdout.print("Error: Mailbox {} is sealed!\n", .{mailbox_num});
                            },
                        }
                    }
                },
                .SealMailbox => {
                    const mailbox_num = try get_mailbox_number();
                    if (chall.seal_mailbox(mailbox_num)) {
                        try stdout.print("Mailbox {} sealed!\n", .{mailbox_num});
                    } else |err| {
                        switch (err) {
                            error.MailboxEmpty => {
                                try stdout.print("Error: Mailbox {} is empty!\n", .{mailbox_num});
                            },
                            error.BadMailbox => {
                                try stdout.print("Error: Mailbox {} is invalid!\n", .{mailbox_num});
                            },
                            else => {
                                return err;
                            },
                        }
                    }
                },
                .StuffSecretMailbox => {
                    if (chall.stuff_secret_mailbox()) {
                        try stdout.print("Secret Envelope Stuffed!\n", .{});
                    } else |err| {
                        switch (err) {
                            error.SecretEnvelopeAlreadyStuffed => {
                                try stdout.print("You can only stuff the secret mailbox once!\n", .{});
                            },
                            else => {
                                return err;
                            }
                        }
                    }
                },
                .Exit => {
                    try stdout.print("Goodbye!\n", .{});
                },
            }
        } else {
            try stdout.print("Invalid Menu Input\n", .{});
        }
    }
}
