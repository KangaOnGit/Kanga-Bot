def open_database(ctx):
    """
    Opens the database file and returns the data. If the file doesn't exist,
    initializes it with default values for a new user.
    """
    try:
        with open('Database.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}  # Initialize with an empty dictionary if file not found

    user_id = str(ctx.author.id)
    if user_id not in data:
        # Initialize new user data with default values
        data[user_id] = {
            'Wallet': 0,
            'Bank': 0,
            'Daily Timer': 0,
            'Daily Streak': 0,
            'Weekly Timer': 0,
            'Rob Timer': 0,
            'Beg Timer': 0,
            'Search Timer': 0,
            'Pray Timer': 0,
            'Status Effects': {},
            'Inventory': {}
        }
        with open('Database.json', 'w') as f:
            json.dump(data, f, indent=4)

    return data


def save_data(data):
    """
    Saves the provided data to the database file.
    """
    with open('Database.json', 'w') as f:
        json.dump(data, f, indent=4)


def remove_expired_status_effects(data, user_id):
    now = get_current_timestamp()
    status_effects = data.get(user_id, {}).get('Status Effects', {})
    if status_effects and now > status_effects.get('Expires', 0):
        data[user_id]['Status Effects'] = {}
        return True
    return False


async def check_cooldown(ctx, user_id, timer_key, cooldown_period, embed_title, embed_description):
    """
    Checks if the user is still under cooldown for a specified action.
    Sends an embed message if they are still on cooldown.
    """
    data = open_database(ctx)
    now = datetime.now(timezone.utc)
    current_timestamp = get_current_timestamp()

    last_timestamp = data[user_id].get(timer_key, 0)
    last_time = datetime.fromtimestamp(
        last_timestamp, tz=timezone.utc) if last_timestamp else now - cooldown_period

    if now - last_time < cooldown_period:
        next_time = last_timestamp + cooldown_period.total_seconds()
        embed = discord.Embed(
            title=embed_title,
            description=embed_description.format(int(next_time)),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return False
    return True


@bot.command(name='daily')
async def daily_reward(ctx):
    """
    Allows users to claim their daily reward. The reward amount can be affected by streak bonuses.
    """
    data = open_database(ctx)
    user_id = str(ctx.author.id)
    user_data = data[user_id]
    user = await bot.fetch_user(ctx.author.id)

    now = datetime.now(timezone.utc)
    current_timestamp = int(now.timestamp())
    daily_cd = timedelta(days=1)  # 24-hour cooldown period
    streak_reset = timedelta(days=2)  # Reset streak after 2 days

    last_claim_timestamp = user_data.get('Daily Timer', 0)
    last_claim_time = datetime.fromtimestamp(
        last_claim_timestamp, tz=timezone.utc) if last_claim_timestamp else now - timedelta(days=2)

    if now - last_claim_time >= daily_cd:
        user_data['Daily Timer'] = current_timestamp

        if now - last_claim_time >= streak_reset:
            data[user_id]['Daily Streak'] = 0

        streak_bonus = 1 + min(data[user_id]['Daily Streak'] * 0.03, 3.0)
        random_reward = rand.randint(1000, 3000)
        total_amount = int(random_reward * streak_bonus)
        user_data['Wallet'] += total_amount
        data[user_id]['Daily Streak'] += 1

        save_data(data)

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Daily Reward",
            description=f"You've claimed your daily reward of {
                total_amount} KanCoins!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Daily Streak: {data[user_id]['Daily Streak']} | Bonus: {
                         data[user_id]['Daily Streak'] * 0.03 * 100}%", icon_url=user.display_avatar.url)

        await ctx.send(embed=embed)
    else:
        next_claim_time = last_claim_time + daily_cd
        next_claim_timestamp = int(next_claim_time.timestamp())

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Daily Reward Not Available",
            description=f"Your daily reward is not ready yet! Return back in <t:{
                next_claim_timestamp}:R>, <t:{next_claim_timestamp}:f>!",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Daily Streak: {data[user_id]['Daily Streak']} | Bonus: {
                         data[user_id]['Daily Streak'] * 0.03 * 100}%", icon_url=user.display_avatar.url)

        await ctx.send(embed=embed)


@bot.command(name='bal')
async def check_balance(ctx):
    """
    Shows the user's current wallet and bank balance.
    """
    data = open_database(ctx)
    user = await bot.fetch_user(ctx.author.id)

    embed = discord.Embed(
        title=f"{ctx.author.name}'s Balance",
        color=discord.Color.blue()
    )
    embed.add_field(name="Wallet:", value=f"{
                    data[str(ctx.author.id)]['Wallet']} KanCoins")
    embed.add_field(name="Bank Account:", value=f"{
                    data[str(ctx.author.id)]['Bank']} KanCoins")
    embed.set_footer(text=f"Requested by {
                     ctx.author.name}", icon_url=user.display_avatar.url)

    await ctx.send(embed=embed)


def get_current_timestamp():
    """
    Returns the current timestamp in seconds.
    """
    return int(datetime.now(timezone.utc).timestamp())


def apply_status_effects(data, user_id, amount, command_type=None):
    """
    Applies status effects to the amount of money.
    """
    status_effect = data[user_id]['Status Effects']

    if command_type in ['beg', 'search'] and status_effect.get('Blessing') == 'Demonic Blessing':
        return amount  # No multiplier applied for 'beg' and 'search' with Demonic Blessing

    if status_effect['Multiplier']:
        multiplier = status_effect['Multiplier']
        amount *= multiplier
    else:
        amount = 1
    return amount


@bot.command(name='rob')
async def rob_people(ctx, target: discord.User):
    """
    Allows users to rob another user with varying success chances based on status effects.
    """
    data = open_database(ctx)
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    if remove_expired_status_effects(data, user_id):
        save_data(data)

    if not await check_cooldown(ctx, user_id, 'Rob Timer', timedelta(minutes=30),
                                f"{ctx.author.name}'s Rob Cooldown",
                                "Don't be so hasty, you can rob again in <t:{}:R>."):
        return

    if target_id not in data:
        await ctx.send("Target user does not have a balance record.")
        return

    if user_id not in data:
        await ctx.send("Your account does not have a balance record.")
        return

    if data[target_id]['Wallet'] <= 0:
        await ctx.send("They're too broke to be robbed.")
        return

    wallet_target = data[target_id].get('Wallet', 0)
    base_wallet_robbed = int(wallet_target * (rand.randint(2, 3) * 0.1))
    wallet_robbed = apply_status_effects(data, user_id, base_wallet_robbed)
    number = rand.randint(0, 10)

    chance_increment = 1
    status_effect = data[user_id].get('Status Effects', {})
    multiplier = 1
    fine_multiplier = 1

    if status_effect.get('Blessing') == 'Demonic Blessing':
        multiplier += 1  # 100% more for robbery
        chance_increment = 1.5
        fine_multiplier = 1.3  # 30% more if fined

    if number < int(2 * chance_increment):
        wallet_robbed = int(wallet_robbed * multiplier)
        data[target_id]['Wallet'] -= wallet_robbed
        data[user_id]['Wallet'] += wallet_robbed
        result_message = f"You've successfully robbed {
            target.name} for {wallet_robbed} KanCoin!"
        data[user_id]['Rob Timer'] = get_current_timestamp()

    elif number > 8:
        # Apply the fine multiplier
        fine = int(data[user_id]['Wallet'] * 0.2 * fine_multiplier)
        data[user_id]['Wallet'] -= fine
        result_message = f"You've been caught! Your fine was {fine} KanCoin."
        data[user_id]['Rob Timer'] = get_current_timestamp()

    else:
        result_message = f"You've failed to rob {target.name}!"
        data[user_id]['Rob Timer'] = get_current_timestamp()

    save_data(data)
    await ctx.send(result_message)


@bot.command(name='beg')
async def beggars_choosers(ctx):
    """
    Allows users to beg for money with varying amounts based on chance and status effects.
    """
    data = open_database(ctx)
    user_id = str(ctx.author.id)

    if remove_expired_status_effects(data, user_id):
        save_data(data)

    if not await check_cooldown(ctx, user_id, 'Beg Timer', timedelta(seconds=15),
                                f"{ctx.author.name}'s Beg Cooldown",
                                "Calm down broke boy, you can beg again <t:{}:R>."):
        return

    number = rand.randint(0, 10)
    beg_money = 0

    if number > 9:
        beg_money = int(rand.randint(1000, 2000) * 1.9)
    elif number < 1:
        beg_money = int(rand.randint(500, 1000) * 1.1)
    else:
        beg_money = int(rand.randint(100, 1000) * 1.3)

    beg_money = apply_status_effects(data, user_id, beg_money, 'beg')

    data[user_id]['Wallet'] += beg_money
    data[user_id]['Beg Timer'] = get_current_timestamp()

    save_data(data)

    embed = discord.Embed(
        title=f"{ctx.author.name}'s Begging Results",
        description=f"You've begged for {beg_money} KanCoins!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


def pray_to_demon():
    chance = rand.random()
    if chance < 0.1:  # 10% chance for a curse
        return "Wrath of the Underworld", 0.3, timedelta(days=1)
    elif chance < 0.2:  # 10% chance for a blessing
        return "Demonic Blessing", 2, timedelta(hours=3)
    else:
        return "I have no mouth and I must scream", 0.8, timedelta(days=1)


def pray_to_god():
    chance = rand.random()
    if chance < 0.05:  # 5% chance of angering the gods
        return "Divine Retribution", 0.8, timedelta(hours=12)
    elif chance < 0.25:  # 20% chance of pleasing the gods
        return "Divine Blessing", 1.25, timedelta(hours=12)
    else:
        return "Devotee", 1.05, timedelta(days=1)
# Pray command


@bot.command(name='pray')
async def pray(ctx, choice: str):
    data = open_database(ctx)
    user_id = str(ctx.author.id)
    now = datetime.now(timezone.utc)
    current_timestamp = get_current_timestamp()
    pray_cd = timedelta(days=1)
    if remove_expired_status_effects(data, user_id):
        save_data(data)

    if not await check_cooldown(ctx, user_id, 'Pray Timer', pray_cd,
                                f"{ctx.author.name}'s Pray Cooldown",
                                "Calm down, you can pray again <t:{}:R>."):
        return

    if choice.lower() == 'demon':
        blessing, multiplier, duration = pray_to_demon()
        data[user_id]['Pray Timer'] = current_timestamp
    elif choice.lower() == 'god':
        blessing, multiplier, duration = pray_to_god()
        data[user_id]['Pray Timer'] = current_timestamp
    else:
        await ctx.send("Please choose either 'demon' or 'god'.")
        return

    expiration_time = current_timestamp + int(duration.total_seconds())
    data[user_id]['Status Effects'] = {
        "Blessing": blessing,
        "Multiplier": multiplier,
        "Expires": expiration_time
    }

    save_data(data)

    embed = discord.Embed(
        title=f"{ctx.author.name}'s Prayer Result",
        description=f"**{blessing}** applied! Multiplier: {
            multiplier}. Duration: <t:{expiration_time}:R>.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Command to check Status


@bot.command(name='check_status')
async def check_status(ctx):
    data = open_database(ctx)
    user_id = str(ctx.author.id)
    if remove_expired_status_effects(data, user_id):
        save_data(data)

    status_effect = data[user_id].get('Status Effects', {})

    if status_effect:
        expiration_time = status_effect['Expires']
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Status",
            description=f"**{status_effect['Blessing']}** active! Multiplier: {
                status_effect['Multiplier']}. Expires in <t:{expiration_time}:R>.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("You have no active status effects.")

# Background task to check status effects every hour


@bot.command(name='search')
async def search(ctx):
    """
    Allows users to search for money with varying success rates and amounts.
    """
    data = open_database(ctx)
    user_id = str(ctx.author.id)
    if remove_expired_status_effects(data, user_id):
        save_data(data)

    if not await check_cooldown(ctx, user_id, 'Search Timer', timedelta(minutes=30),
                                f"{ctx.author.name}'s Search Cooldown",
                                "You can search again in <t:{}:R>."):
        return

    number = rand.randint(0, 10)
    search_money = 0

    if number > 9:
        search_money = int(rand.randint(1000, 2000) * 1.5)
    elif number < 1:
        search_money = int(rand.randint(500, 1000) * 1.2)
    else:
        search_money = int(rand.randint(100, 500) * 1.1)

    search_money = apply_status_effects(data, user_id, search_money, 'search')

    data[user_id]['Wallet'] += search_money
    data[user_id]['Search Timer'] = get_current_timestamp()

    save_data(data)

    embed = discord.Embed(
        title=f"{ctx.author.name}'s Search Results",
        description=f"You've found {search_money} KanCoins!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
