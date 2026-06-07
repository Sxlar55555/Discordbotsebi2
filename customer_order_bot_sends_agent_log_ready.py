import os
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands

# ============================================================
# EDIT THESE
# ============================================================
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1512886556711714897  # server ID

# Channel where the order ticket panel should be sent
TICKET_PANEL_CHANNEL_ID = 1512901490929569882  # order ticket panel channel

# Agent server webhook. Create this webhook in an agent-server log channel.
AGENT_LOG_WEBHOOK_URL = "https://discord.com/api/webhooks/1513215864919294097/lSmdYUU902oCDbV0w9F9Na3kqCYqgwMdSP38y8MhraI6GBVVF3tvDG8A5RSuTAv2qAoA"

# Owner/staff who gets added and pinged in every ticket
OWNER_ID = 1498383669520498888

# Optional category where order ticket channels are created
TICKET_CATEGORY_ID = 0

# Prices
ICON_PRICE = 150
THUMBNAIL_PRICE = 200
PAYMENT_GAME_LINK = "https://www.roblox.com/share?code=22854b4bfefdf146b8cac6d21994473e&type=ExperienceDetails&stamp=1780845321017"

# ============================================================
# BOT CODE
# ============================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def send_agent_server_order_log(customer_username, creator, icons, thumbnails, total, ticket_channel):
    """Sends the customer order total to the agent server using a webhook."""
    if AGENT_LOG_WEBHOOK_URL == "PASTE_AGENT_SERVER_LOG_WEBHOOK_URL_HERE" or not AGENT_LOG_WEBHOOK_URL:
        print("⚠️ Agent log webhook is not set, skipping agent-server order log.")
        return

    payload = {
        "content": "New customer order saved for agent payout lookup.",
        "embeds": [
            {
                "title": "🧾 Customer Order Payment Log",
                "color": 3447003,
                "fields": [
                    {"name": "Roblox Username", "value": f"`{customer_username}`", "inline": False},
                    {"name": "Customer Discord", "value": f"{creator} / `{creator.id}`", "inline": False},
                    {"name": "Icons", "value": f"`{icons}`", "inline": True},
                    {"name": "Thumbnails", "value": f"`{thumbnails}`", "inline": True},
                    {"name": "Total Paid", "value": f"`{total} Robux`", "inline": False},
                    {"name": "Customer Ticket", "value": f"{ticket_channel.mention}", "inline": False}
                ],
                "footer": {"text": "ORDER_LOOKUP_LOG"}
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(AGENT_LOG_WEBHOOK_URL, json=payload) as response:
            if response.status >= 300:
                print(f"❌ Agent webhook failed: {response.status} {await response.text()}")
            else:
                print("✅ Sent order total to agent server log.")


class OrderModal(discord.ui.Modal, title="Create Order Ticket"):
    roblox_username = discord.ui.TextInput(
        label="Roblox username",
        placeholder="Enter your Roblox username...",
        required=True,
        max_length=100
    )

    icon_amount = discord.ui.TextInput(
        label="How many icons?",
        placeholder="Enter 0 if you do not want icons",
        required=True,
        max_length=3,
        default="0"
    )

    thumbnail_amount = discord.ui.TextInput(
        label="How many thumbnails?",
        placeholder="Enter 0 if you do not want thumbnails",
        required=True,
        max_length=3,
        default="0"
    )

    extra_info = discord.ui.TextInput(
        label="Extra info / details",
        placeholder="Describe what you want...",
        required=False,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            guild = interaction.guild
            creator = interaction.user

            if guild is None:
                await interaction.followup.send("❌ This only works inside a server.", ephemeral=True)
                return

            try:
                icons = int(str(self.icon_amount.value).strip())
                thumbnails = int(str(self.thumbnail_amount.value).strip())
            except ValueError:
                await interaction.followup.send("❌ Icon amount and thumbnail amount must be numbers.", ephemeral=True)
                return

            if icons < 0 or thumbnails < 0:
                await interaction.followup.send("❌ Amounts cannot be negative.", ephemeral=True)
                return

            if icons == 0 and thumbnails == 0:
                await interaction.followup.send("❌ You must order at least 1 icon or 1 thumbnail.", ephemeral=True)
                return

            if icons > 50 or thumbnails > 50:
                await interaction.followup.send("❌ Max amount is 50 for each item.", ephemeral=True)
                return

            owner = guild.get_member(OWNER_ID)
            if owner is None:
                try:
                    owner = await guild.fetch_member(OWNER_ID)
                except Exception:
                    await interaction.followup.send("❌ I could not find the owner in this server. Check OWNER_ID.", ephemeral=True)
                    return

            bot_member = guild.me or guild.get_member(bot.user.id)

            if not bot_member.guild_permissions.manage_channels:
                await interaction.followup.send(
                    "❌ I need **Manage Channels** permission to create tickets.",
                    ephemeral=True
                )
                return

            safe_name = creator.name.lower().replace(" ", "-")
            channel_name = f"order-{safe_name}"

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                creator: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),
                owner: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    attach_files=True,
                    embed_links=True
                ),
                bot_member: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
            }

            category = None
            if TICKET_CATEGORY_ID:
                category = guild.get_channel(TICKET_CATEGORY_ID)

            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                reason=f"Order ticket created by {creator}"
            )

            icon_total = icons * ICON_PRICE
            thumbnail_total = thumbnails * THUMBNAIL_PRICE
            total = icon_total + thumbnail_total

            order_lines = []
            if icons:
                order_lines.append(f"• **Icon** x{icons} = **{icon_total} Robux**")
            if thumbnails:
                order_lines.append(f"• **Thumbnail** x{thumbnails} = **{thumbnail_total} Robux**")

            embed = discord.Embed(
                title="🎫 New Order Ticket",
                description="A new customer order ticket has been created.",
                color=discord.Color.blue()
            )

            embed.add_field(name="Customer", value=f"{creator.mention}\n`{creator.id}`", inline=False)
            embed.add_field(name="Roblox Username", value=f"`{self.roblox_username.value}`", inline=False)
            embed.add_field(name="Prices", value=f"• Icon: **{ICON_PRICE} Robux** each\n• Thumbnail: **{THUMBNAIL_PRICE} Robux** each", inline=False)
            embed.add_field(name="Order", value="\n".join(order_lines), inline=False)
            embed.add_field(name="Total Price", value=f"**{total} Robux**", inline=False)
            embed.add_field(name="Payment Game", value=f"[Click here to pay Robux]({PAYMENT_GAME_LINK})", inline=False)

            if self.extra_info.value:
                embed.add_field(name="Extra Info", value=self.extra_info.value, inline=False)

            embed.set_footer(text="Please wait for the owner/staff to respond.")

            await ticket_channel.send(
                content=f"<@{OWNER_ID}> New order ticket from {creator.mention}.",
                embed=embed,
                view=CloseTicketView()
            )

            await send_agent_server_order_log(self.roblox_username.value, creator, icons, thumbnails, total, ticket_channel)

            try:
                await owner.send(
                    f"📩 New order ticket created.\n"
                    f"Server: **{guild.name}**\n"
                    f"Customer: {creator} / `{creator.id}`\n"
                    f"Roblox username: `{self.roblox_username.value}`\n"
                    f"Icons: `{icons}`\n"
                    f"Thumbnails: `{thumbnails}`\n"
                    f"Total: `{total} Robux`\n"
                    f"Payment game: {PAYMENT_GAME_LINK}\n"
                    f"Ticket: {ticket_channel.mention}"
                )
            except discord.Forbidden:
                pass

            await interaction.followup.send(f"✅ Order ticket created: {ticket_channel.mention}", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I do not have permission to create the ticket channel. Give me **Manage Channels** and make sure my role is high enough.",
                ephemeral=True
            )
        except Exception as error:
            await interaction.followup.send(
                f"❌ Error while creating ticket: `{type(error).__name__}: {error}`",
                ephemeral=True
            )


class OrderTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Order", style=discord.ButtonStyle.primary, emoji="🛒", custom_id="order_ticket_button")
    async def order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_order_ticket_button")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only the owner or staff can close this ticket.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
        await interaction.channel.delete(reason=f"Order ticket closed by {interaction.user}")


@bot.event
async def on_ready():
    bot.add_view(OrderTicketView())
    bot.add_view(CloseTicketView())

    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    else:
        synced = await bot.tree.sync()

    print(f"✅ Logged in as {bot.user}")
    print(f"✅ Synced {len(synced)} slash commands")
    print("✅ Order ticket bot is running")


@bot.tree.command(name="setup_order_tickets", description="Send the order ticket panel.")
async def setup_order_tickets(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only the owner/admin can use this.", ephemeral=True)
        return

    channel = interaction.channel

    if TICKET_PANEL_CHANNEL_ID:
        found_channel = interaction.guild.get_channel(TICKET_PANEL_CHANNEL_ID)
        if found_channel:
            channel = found_channel

    embed = discord.Embed(
        title="🛒 Order Tickets",
        description=(
            "Click **Order** below to create a private order ticket.\n\n"
            "**Prices:**\n"
            f"• Icon = **{ICON_PRICE} Robux**\n"
            f"• Thumbnail = **{THUMBNAIL_PRICE} Robux**\n\n"
            "You can order one item or multiple items, and choose how many of each you want."
        ),
        color=discord.Color.blue()
    )

    embed.set_footer(text="After clicking Order, fill in the amounts you want.")

    await channel.send(embed=embed, view=OrderTicketView())
    await interaction.response.send_message(f"✅ Order ticket panel sent in {channel.mention}.", ephemeral=True)


if TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE" or not TOKEN:
    raise RuntimeError("Paste your bot token at the top of the file.")

bot.run(TOKEN)

