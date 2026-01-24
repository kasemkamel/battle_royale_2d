# server\network\packet_handler.py
"""
Server Packet Handler
Routes incoming packets to appropriate handler methods.
"""

import math
import time
from shared.enums import PacketType
from shared.packets import Packet, LoginResponse, RegisterResponse, LobbyState
from server.network.server_socket import ClientConnection


class ServerPacketHandler:
    """Handles incoming packets from clients."""
    
    def __init__(self, server):
        """
        server: The main GameServer instance with auth, lobby, etc.
        """
        self.server = server
        self.chanelling_clicks_activate = False
    
    async def handle_packet(self, client: ClientConnection, packet: Packet):
        """Route packet to appropriate handler."""
        handlers = {
            PacketType.LOGIN_REQUEST: self._handle_login,
            PacketType.REGISTER_REQUEST: self._handle_register,
            PacketType.LOGOUT: self._handle_logout,
            PacketType.JOIN_LOBBY: self._handle_join_lobby,
            PacketType.LEAVE_LOBBY: self._handle_leave_lobby,
            PacketType.PLAYER_READY: self._handle_player_ready,
            PacketType.PLAYER_INPUT: self._handle_player_input,
            PacketType.USE_SKILL: self._handle_use_skill,
            PacketType.STOP_CHANNELING: self._handle_stop_channeling,
            PacketType.CHAT_MESSAGE: self._handle_chat,
            PacketType.PING: self._handle_ping,
            PacketType.GET_ALL_SKILLS: self._handle_get_all_skills,
            PacketType.UPDATE_SKILL_LOADOUT: self._handle_update_skill_loadout,
        }
        
        handler = handlers.get(packet.type)
        if handler:
            await handler(client, packet)
        else:
            print(f"[Server] Unhandled packet type: {packet.type}")
    
    async def _handle_login(self, client: ClientConnection, packet: Packet):
        """Handle login request."""
        username = packet.data.get("username")
        password = packet.data.get("password")
        
        success, message, user = self.server.authenticator.login(username, password)
        
        if success:
            client.user_id = user.user_id
            response = LoginResponse(
                success=True,
                message=message,
                user_id=user.user_id,
                stats=user.stats
            )
            # Add skill loadout to response
            response.data["skill_loadout"] = user.skill_loadout
        else:
            response = LoginResponse(success=False, message=message)
        
        await client.send(response)
    
    async def _handle_register(self, client: ClientConnection, packet: Packet):
        """Handle registration request."""
        username = packet.data.get("username")
        password = packet.data.get("password")
        email = packet.data.get("email", "")
        
        success, message, user = self.server.authenticator.register(username, password, email)
        
        response = RegisterResponse(success=success, message=message)
        await client.send(response)
    
    async def _handle_logout(self, client: ClientConnection, packet: Packet):
        """Handle logout."""
        if client.user_id:
            self.server.authenticator.logout(client.user_id)
            client.user_id = None
    
    async def _handle_join_lobby(self, client: ClientConnection, packet: Packet):
        """Handle join lobby request."""
        if not client.user_id:
            return
        
        # If client already has a player_id, don't add again
        if client.player_id:
            print(f"[Server] Client {client.conn_id} already has player_id {client.player_id}")
            await self._broadcast_lobby_state()
            return
        
        # Add player to lobby
        player = self.server.lobby_manager.add_player(client.user_id, client.conn_id)
        if player:
            client.player_id = player.player_id
            
            # Send lobby state to all players
            await self._broadcast_lobby_state()
    
    async def _handle_leave_lobby(self, client: ClientConnection, packet: Packet):
        """Handle leave lobby request."""
        if client.player_id:
            self.server.lobby_manager.remove_player(client.player_id)
            client.player_id = None
            
            await self._broadcast_lobby_state()
    
    async def _handle_player_ready(self, client: ClientConnection, packet: Packet):
        """Handle player ready toggle."""
        if not client.player_id:
            return
        
        ready = packet.data.get("ready", True)
        self.server.lobby_manager.set_player_ready(client.player_id, ready)
        
        await self._broadcast_lobby_state()
    
    async def _handle_player_input(self, client: ClientConnection, packet: Packet):
        """Handle player input during gameplay."""
        if not client.player_id:
            return
        
        # Forward to match manager
        move_x = packet.data.get("move_x", 0)
        move_y = packet.data.get("move_y", 0)
        mouse_x = packet.data.get("mouse_x", 0)
        mouse_y = packet.data.get("mouse_y", 0)
        actions = packet.data.get("actions", {})
        
        # Update player input in active match
        if self.server.match_manager.active_match:
            match = self.server.match_manager.active_match
            player = match.players.get(client.player_id)
            if player:
                player.set_input(move_x, move_y, mouse_x, mouse_y, actions)
    
    async def _handle_use_skill(self, client: ClientConnection, packet: Packet):
        """Handle skill casting."""
        if not client.player_id or not client.user_id:
            return
        
        skill_index = packet.data.get("skill_index")
        mouse_x = packet.data.get("mouse_world_x", 0)
        mouse_y = packet.data.get("mouse_world_y", 0)
        
        # Get player from active match
        if not self.server.match_manager.active_match:
            return
        
        match = self.server.match_manager.active_match
        player = match.players.get(client.player_id)
        
        if not player:
            return
        
        # Get skill from player's equipped skills (each player has their own instances)
        if skill_index >= len(player.skills):
            print(f"[Server] {player.username} tried to use skill {skill_index} but only has {len(player.skills)} skills")
            return
        
        skill = player.skills[skill_index]
        
        # Check if can cast (mana, cooldown)
        can_cast, reason = skill.can_cast(player.mana)
        if not can_cast:
            print(f"[Server] {player.username} cannot cast {skill.name}: {reason}")
            return
        
        from shared.skill_system import SkillCategory
    
        if skill.category == SkillCategory.CHANNELING:
            # Start channeling
            if not player.is_channeling:
                # Consume NO mana upfront (drained per second)
                player.start_channeling(skill_index, mouse_x, mouse_y)
                
                # Cast to initialize
                player_pos = (player.x, player.y)
                target_pos = (mouse_x, mouse_y)
                effect_data = skill.cast(player_pos, target_pos)
                
                print(f"[Server] {player.username} started channeling {skill.name}")
            else:
                # Already channeling, update target position
                player.channel_target_x = mouse_x
                player.channel_target_y = mouse_y
            
            return
        
        # Consume mana
        player.mana -= skill.mana_cost
        
        # Cast the skill
        player_pos = (player.x, player.y)
        target_pos = (mouse_x, mouse_y)
        effect_data = skill.cast(player_pos, target_pos)
        
        print(f"[Server] {player.username} cast {skill.name} (mana: {player.mana:.1f}, cooldown: {skill.cooldown}s)")
        
        # Apply skill effects immediately (simplified for now)
        self._apply_skill_effects(match, player, skill, effect_data)
    
    def _apply_skill_effects(self, match, caster, skill, effect_data):
        """Apply skill effects to targets."""
        category = skill.category.name
        
        if category == "SKILLSHOT":
            # CREATE PROJECTILE instead of instant raycast
            from server.models.projectile import Projectile
            
            projectile = Projectile(
                projectile_id=0,  # Will be set by match.add_projectile()
                skill_id=skill.skill_id,
                caster_id=caster.player_id,
                x=effect_data["start_x"],
                y=effect_data["start_y"],
                direction_x=effect_data["direction_x"],
                direction_y=effect_data["direction_y"],
                speed=effect_data["speed"],
                damage=effect_data["damage"],
                max_range=effect_data["max_range"],
                width=effect_data["width"],
                piercing=effect_data.get("piercing", False)
            )
            
            match.add_projectile(projectile)
            print(f"[Skill] {caster.username} fired {skill.name} projectile")
        
        elif category == "HOMING":
            # CREATE HOMING PROJECTILE instead of instant hit
            from server.models.projectile import HomingProjectile
            
            projectile = HomingProjectile(
                projectile_id=0,
                skill_id=skill.skill_id,
                caster_id=caster.player_id,
                x=caster.x,
                y=caster.y,
                direction_x=effect_data["direction_x"],
                direction_y=effect_data["direction_y"],
                speed=effect_data["speed"],
                damage=effect_data["damage"],
                turn_rate=effect_data["turn_rate"],
                max_lifetime=effect_data["max_lifetime"]
            )
            
            match.add_projectile(projectile)
            print(f"[Skill] {caster.username} launched homing {skill.name}")
        
        elif category == "AOE":
            # Damage all players in radius
            center_x = effect_data["center_x"]
            center_y = effect_data["center_y"]
            radius = effect_data["radius"]
            damage = effect_data["damage"]
            
            for player in match.players.values():
                if player.player_id == caster.player_id:
                    continue  # Don't damage self
                
                dx = player.x - center_x
                dy = player.y - center_y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= radius:
                    player.take_damage(damage, caster.player_id)
                    print(f"[Skill] AOE hit {player.username} for {damage} damage")
        
        elif category == "RANGEBASED":
            # Damage all players in radius around caster
            radius = effect_data["radius"]
            damage = effect_data["damage"]
            
            for player in match.players.values():
                if player.player_id == caster.player_id:
                    continue
                
                dx = player.x - caster.x
                dy = player.y - caster.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= radius:
                    player.take_damage(damage, caster.player_id)
                    print(f"[Skill] Range hit {player.username} for {damage} damage")
        
        elif category == "CHANNELING":
            # Start channeling state (continuous damage)
            # For now, treat as instant damage in cone
            # TODO: Implement proper channeling with continuous damage

            if not self.chanelling_clicks_activate:
                self.chanelling_clicks_activate == True
                damage = effect_data.get("damage", 2)
                max_range = effect_data["max_range"]
                dir_x = effect_data["direction_x"]
                dir_y = effect_data["direction_y"]
                for player in match.players.values():
                    if player.player_id == caster.player_id:
                        continue
                    
                    # Check if in beam direction
                    to_player_x = player.x - caster.x
                    to_player_y = player.y - caster.y
                    distance = math.sqrt(to_player_x**2 + to_player_y**2)
                    
                    if distance > max_range:
                        continue
                    
                    # Normalize
                    if distance > 0:
                        to_player_x /= distance
                        to_player_y /= distance
                    
                    # Check angle (dot product)
                    dot = to_player_x * dir_x + to_player_y * dir_y
                    
                    if dot > 0.95:  # ~18 degree cone
                        player.continuous_damage_tick(damage * 0.5, caster.player_id)  # Half damage per tick
                        print(f"[Skill] Channeling hit {player.username} for {damage * 0.5} damage")
                        # -> Allow multiple hits in cone
            else:
                self.chanelling_clicks_activate == False

        
        elif category == "DEFENSIVE":
            # Apply shield buff to caster
            shield_amount = effect_data["shield_amount"]
            shield_max_hits = effect_data["max_hits"]
            shield_duration = effect_data["duration"]
            caster.apply_defense(shield_amount, max_hits=shield_max_hits, duration=shield_duration)
            print(f"[Skill] Applied {shield_amount} shield to {caster.username}")
        
        elif category == "CROWD_CONTROL":
            # Apply CC to all in radius
            center_x = effect_data["center_x"]
            center_y = effect_data["center_y"]
            radius = effect_data["radius"]
            cc_type = effect_data["cc_type"]
            duration = effect_data["duration"]
            
            for player in match.players.values():
                if player.player_id == caster.player_id:
                    continue
                
                dx = player.x - center_x
                dy = player.y - center_y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= radius:
                    player.apply_crowd_control(cc_type, duration)
                    print(f"[Skill] Applied {cc_type} to {player.username}")
        
        elif category == "PASSIVE":
            # Passives are applied automatically on match start
            # No cast effects needed, already active
            print(f"[Skill] Passive {skill.name} is always active (bonuses already applied)")
        
        elif category == "HEAL":
            # Heal skills - restore health to caster and/or allies
            heal_amount = effect_data["heal_amount"]
            center_x = effect_data["center_x"]
            center_y = effect_data["center_y"]
            radius = effect_data["radius"]
            self_only = effect_data["self_only"]
            
            if self_only or radius == 0:
                # Heal only caster
                caster.apply_heal(heal_amount)
            else:
                # Heal caster and nearby allies
                caster.apply_heal(heal_amount)
                
                # TODO: Implement team system to heal allies only
                # For now, heal all nearby players (including enemies - be careful!)
                for player in match.players.values():
                    if player.player_id == caster.player_id:
                        continue
                    
                    dx = player.x - center_x
                    dy = player.y - center_y
                    distance = math.sqrt(dx**2 + dy**2)
                    
                    if distance <= radius:
                        player.apply_heal(heal_amount)
        
        elif category == "DISAPPEAR":
            # Invisibility/stealth
            duration = effect_data["duration"]
            speed_bonus = effect_data["speed_bonus"]
            
            caster.apply_invisibility(duration, speed_bonus)
        
        elif category == "DASH":
            # Skill-based dash/blink
            direction_x = effect_data["direction_x"]
            direction_y = effect_data["direction_y"]
            distance = effect_data["distance"]
            instant = effect_data["instant"]
            mana_cost = skill.mana_cost
            if instant:
                if caster.can_teleport(mana_cost):
                    # Teleport
                    caster.teleport(distance, mana_cost)
            else:
                # Fast dash (similar to space dash but with skill distance)
                caster.dash_direction_x = direction_x
                caster.dash_direction_y = direction_y
                caster.is_dashing = True
                caster.dash_end_time = time.time() + 0.3  # Dash for 0.3 seconds
                print(f"[Skill] {caster.username} dashed")
        
        elif category == "MANA_REGAIN":
            # Restore mana
            mana_amount = effect_data["mana_amount"]
            over_time = effect_data["over_time"]
            
            if over_time:
                # TODO: Implement mana regen over time
                # For now, instant restoration
                caster.restore_mana(mana_amount)
            else:
                # Instant mana restoration
                caster.restore_mana(mana_amount)
    
    async def _handle_chat(self, client: ClientConnection, packet: Packet):
        """Handle chat message."""
        # Broadcast chat to all clients
        await self.server.socket.broadcast(packet)
    
    async def _handle_ping(self, client: ClientConnection, packet: Packet):
        """Handle ping request."""
        pong = Packet(PacketType.PONG, {"timestamp": packet.data.get("timestamp")})
        await client.send(pong)
    
    async def _handle_get_all_skills(self, client: ClientConnection, packet: Packet):
        """Send all available skills to client."""
        all_skills = self.server.skill_database.get_all_skills()
        
        response = Packet(PacketType.ALL_SKILLS_RESPONSE, {
            "skills": all_skills
        })
        await client.send(response)
    
    async def _handle_update_skill_loadout(self, client: ClientConnection, packet: Packet):
        """Update player's skill loadout."""
        if not client.user_id:
            return
        
        skill_ids = packet.data.get("skill_loadout", [])
        
        # Validate loadout
        is_valid, error_msg = self.server.skill_database.validate_skill_loadout(skill_ids)
        
        if not is_valid:
            response = Packet(PacketType.SKILL_LOADOUT_RESPONSE, {
                "success": False,
                "message": error_msg
            })
            await client.send(response)
            return
        
        # Update in database
        self.server.database.update_skill_loadout(client.user_id, skill_ids)
        
        # Update user session
        user = self.server.authenticator.get_session(client.user_id)
        if user:
            user.skill_loadout = skill_ids
        
        response = Packet(PacketType.SKILL_LOADOUT_RESPONSE, {
            "success": True,
            "message": "Skill loadout updated",
            "skill_loadout": skill_ids
        })
        await client.send(response)
    
    async def _broadcast_lobby_state(self):
        """Send lobby state to all lobby players."""
        lobby_data = self.server.lobby_manager.get_lobby_state()
        lobby_packet = LobbyState(
            players=lobby_data["players"],
            match_starting=lobby_data["match_starting"],
            countdown=lobby_data["countdown"]
        )
        await self.server.socket.broadcast(lobby_packet)

    async def _handle_stop_channeling(self, client: ClientConnection, packet: Packet):
        """Handle stopping channeling skills."""
        if not client.player_id or not client.user_id:
            return
        
        if not self.server.match_manager.active_match:
            return
        
        match = self.server.match_manager.active_match
        player = match.players.get(client.player_id)
        
        if player and player.is_channeling:
            player.stop_channeling()
            print(f"[Server] {player.username} stopped channeling")



