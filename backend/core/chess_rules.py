"""
Chess Rules Engine
Handles classical chess move validation, check detection, and game state logic
"""
from typing import List, Dict, Optional, Tuple
from backend.db.neo4j_client import Neo4jClient
from backend.utils.logger_factory import get_module_logger, debug_trace, log_game_event

logger = get_module_logger()


class ChessRules:
    """Classical chess rules engine"""
    
    def __init__(self, db: Neo4jClient):
        self.db = db
        logger.info("ChessRules initialized")
    
    def is_valid_move(
        self,
        game_id: str,
        piece_id: str,
        from_square: str,
        to_square: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a move is legal according to chess rules
        
        Returns:
            (is_valid, error_message)
        """
        debug_trace(f"Validating move for {piece_id}: {from_square} -> {to_square}")
        
        # Get piece info
        piece_data = self.db.get_piece_state(piece_id)
        if not piece_data:
            logger.warning(f"Piece {piece_id} not found during move validation")
            return False, f"Piece {piece_id} not found"
        
        piece_type = piece_data['type']
        piece_color = piece_data['color']
        
        # Check if square is occupied by own piece
        target_piece = self._get_piece_at_square(game_id, to_square)
        if target_piece and target_piece['color'] == piece_color:
            logger.debug(f"Invalid move: cannot capture own piece at {to_square}")
            return False, "Cannot capture own piece"
        
        # Validate move pattern for piece type
        if not self._is_valid_move_pattern(piece_type, from_square, to_square, piece_data, game_id):
            logger.debug(f"Invalid move pattern for {piece_type}: {from_square} -> {to_square}")
            return False, f"Invalid move pattern for {piece_type}"
        
        # Check path obstruction (except knights)
        if piece_type != 'knight':
            if self._is_path_blocked(game_id, from_square, to_square):
                logger.debug(f"Path blocked for move: {from_square} -> {to_square}")
                return False, "Path is blocked"
        
        # Check if move puts/leaves own king in check
        if self._would_be_in_check_after_move(game_id, piece_id, from_square, to_square):
            logger.debug(f"Move would leave {piece_data['color']} king in check")
            return False, "Move would leave king in check"
        
        logger.debug(f"Move validated successfully: {piece_id} {from_square} -> {to_square}")
        return True, None
    
    def _is_valid_move_pattern(
        self,
        piece_type: str,
        from_square: str,
        to_square: str,
        piece_data: Dict,
        game_id: str = None
    ) -> bool:
        """Validate move pattern for piece type"""
        debug_trace(f"Validating move pattern for {piece_type}: {from_square} -> {to_square}")
        
        from_file, from_rank = ord(from_square[0]), int(from_square[1])
        to_file, to_rank = ord(to_square[0]), int(to_square[1])
        
        file_diff = abs(to_file - from_file)
        rank_diff = abs(to_rank - from_rank)
        
        if piece_type == 'pawn':
            return self._is_valid_pawn_move(from_square, to_square, piece_data, game_id)
        
        elif piece_type == 'knight':
            valid = (file_diff == 2 and rank_diff == 1) or (file_diff == 1 and rank_diff == 2)
            logger.debug(f"Knight move validation: {valid}")
            return valid
        
        elif piece_type == 'bishop':
            valid = file_diff == rank_diff and file_diff > 0
            logger.debug(f"Bishop move validation: {valid}")
            return valid
        
        elif piece_type == 'rook':
            valid = (file_diff == 0 and rank_diff > 0) or (rank_diff == 0 and file_diff > 0)
            logger.debug(f"Rook move validation: {valid}")
            return valid
        
        elif piece_type == 'queen':
            valid = (file_diff == rank_diff and file_diff > 0) or \
                   (file_diff == 0 and rank_diff > 0) or \
                   (rank_diff == 0 and file_diff > 0)
            logger.debug(f"Queen move validation: {valid}")
            return valid
        
        elif piece_type == 'king':
            valid = file_diff <= 1 and rank_diff <= 1 and (file_diff + rank_diff > 0)
            logger.debug(f"King move validation: {valid}")
            return valid
        
        elif piece_type == 'observer':
            # Observer moves like a king (1 square in any direction)
            valid = file_diff <= 1 and rank_diff <= 1 and (file_diff + rank_diff > 0)
            logger.debug(f"Observer move validation: {valid}")
            return valid
        
        logger.debug(f"Unknown piece type: {piece_type}")
        return False
    
    def _is_valid_pawn_move(
        self,
        from_square: str,
        to_square: str,
        piece_data: Dict,
        game_id: str = None
    ) -> bool:
        """Validate pawn move (including forward, capture, double-push)"""
        debug_trace(f"Validating pawn move: {from_square} -> {to_square}")
        
        from_file, from_rank = ord(from_square[0]), int(from_square[1])
        to_file, to_rank = ord(to_square[0]), int(to_square[1])
        
        color = piece_data['color']
        move_count = piece_data.get('move_count', 0)
        
        direction = 1 if color == 'white' else -1
        rank_diff = (to_rank - from_rank) * direction
        file_diff = abs(to_file - from_file)
        
        # Forward move
        if file_diff == 0:
            if rank_diff == 1:
                logger.debug("Valid pawn forward move")
                return True
            # Double push from starting position
            if rank_diff == 2 and move_count == 0:
                logger.debug("Valid pawn double push")
                return True
        
        # Capture (diagonal)
        if file_diff == 1 and rank_diff == 1:
            # Check if target square has enemy piece
            if game_id:
                target_piece = self._get_piece_at_square(game_id, to_square)
                if target_piece and target_piece['color'] != piece_data['color']:
                    logger.debug("Valid pawn capture move")
                    return True
                else:
                    logger.debug("Invalid pawn capture: no enemy piece at target square")
                    return False
            else:
                # If no game_id provided, assume capture is valid (for move pattern checking)
                logger.debug("Valid pawn capture move (no validation)")
                return True
        
        logger.debug(f"Invalid pawn move: rank_diff={rank_diff}, file_diff={file_diff}")
        return False
    
    def _is_path_blocked(
        self,
        game_id: str,
        from_square: str,
        to_square: str
    ) -> bool:
        """Check if path between squares is blocked"""
        debug_trace(f"Checking path blockage: {from_square} -> {to_square}")
        
        from_file, from_rank = ord(from_square[0]), int(from_square[1])
        to_file, to_rank = ord(to_square[0]), int(to_square[1])
        
        file_step = 0 if from_file == to_file else (1 if to_file > from_file else -1)
        rank_step = 0 if from_rank == to_rank else (1 if to_rank > from_rank else -1)
        
        current_file = from_file + file_step
        current_rank = from_rank + rank_step
        
        while current_file != to_file or current_rank != to_rank:
            square = chr(current_file) + str(current_rank)
            piece = self._get_piece_at_square(game_id, square)
            if piece:
                logger.debug(f"Path blocked at {square} by {piece['id']}")
                return True
            
            current_file += file_step
            current_rank += rank_step
        
        logger.debug(f"Path clear: {from_square} -> {to_square}")
        return False
    
    def _get_piece_at_square(self, game_id: str, square: str) -> Optional[Dict]:
        """Get piece at given square (classical position only)"""
        debug_trace(f"Getting piece at square {square}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece)-[:BELONGS_TO]->(g)
        WHERE p.captured = false
        MATCH (p)-[:OCCUPIES]->(pos:Position {square: $square, is_ghost: false})
        RETURN p
        """
        
        results = self.db.execute_query(query, {
            'game_id': game_id,
            'square': square
        })
        
        if results:
            piece = dict(results[0]['p'])
            logger.debug(f"Found piece {piece['id']} at {square}")
            return piece
        
        logger.debug(f"No piece found at {square}")
        return None
    
    def get_valid_moves(self, game_id: str, piece_id: str) -> Dict:
        """
        Get all valid moves for a piece
        
        Returns:
            {
                'valid_moves': [...],
                'quantum_moves': [...],
                'capture_moves': [...]
            }
        """
        debug_trace(f"Getting valid moves for piece {piece_id}")
        
        piece_data = self.db.get_piece_state(piece_id)
        if not piece_data or piece_data.get('captured'):
            logger.debug(f"Piece {piece_id} not found or captured")
            return {'valid_moves': [], 'quantum_moves': [], 'capture_moves': []}
        
        # Get current position (first non-ghost position)
        current_pos = None
        for pos in piece_data['positions']:
            if not pos['is_ghost']:
                current_pos = pos['square']
                break
        
        if not current_pos:
            logger.debug(f"No current position found for piece {piece_id}")
            return {'valid_moves': [], 'quantum_moves': [], 'capture_moves': []}
        
        # Generate all possible moves for piece type
        all_squares = self._generate_all_possible_moves(
            piece_data['type'],
            current_pos,
            piece_data
        )
        
        # Filter by chess rules
        valid_moves = []
        capture_moves = []
        
        for square in all_squares:
            is_valid, _ = self.is_valid_move(game_id, piece_id, current_pos, square)
            if is_valid:
                valid_moves.append(square)
                
                # Check if it's a capture
                if self._get_piece_at_square(game_id, square):
                    capture_moves.append(square)
        
        # Determine which moves trigger quantum effects
        quantum_moves = []
        if piece_data['quantum_ability']:
            from backend.core.quantum_engine import QuantumEngine
            qe = QuantumEngine(self.db)
            
            for move in valid_moves:
                if qe.should_trigger_superposition(
                    piece_data['type'],
                    current_pos,
                    move
                ):
                    quantum_moves.append(move)
        
        logger.debug(f"Found {len(valid_moves)} valid moves, {len(quantum_moves)} quantum moves, {len(capture_moves)} captures for {piece_id}")
        
        return {
            'valid_moves': valid_moves,
            'quantum_moves': quantum_moves,
            'capture_moves': capture_moves
        }
    
    def _generate_all_possible_moves(
        self,
        piece_type: str,
        current_square: str,
        piece_data: Dict
    ) -> List[str]:
        """Generate all geometrically possible moves (before rule validation)"""
        debug_trace(f"Generating possible moves for {piece_type} at {current_square}")
        
        file, rank = ord(current_square[0]), int(current_square[1])
        moves = []
        
        if piece_type == 'knight':
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            for df, dr in knight_moves:
                new_file, new_rank = file + df, rank + dr
                if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                    moves.append(chr(new_file) + str(new_rank))
        
        elif piece_type in ['bishop', 'rook', 'queen']:
            directions = []
            if piece_type in ['bishop', 'queen']:
                directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
            if piece_type in ['rook', 'queen']:
                directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
            
            for df, dr in directions:
                for i in range(1, 8):
                    new_file, new_rank = file + (df * i), rank + (dr * i)
                    if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                        moves.append(chr(new_file) + str(new_rank))
                    else:
                        break
        
        elif piece_type == 'pawn':
            color = piece_data['color']
            direction = 1 if color == 'white' else -1
            
            # Forward moves
            forward_rank = rank + direction
            if 1 <= forward_rank <= 8:
                moves.append(chr(file) + str(forward_rank))
            
            # Double push
            if piece_data.get('move_count', 0) == 0:
                double_rank = rank + (2 * direction)
                if 1 <= double_rank <= 8:
                    moves.append(chr(file) + str(double_rank))
            
            # Captures
            for df in [-1, 1]:
                new_file = file + df
                if ord('a') <= new_file <= ord('h') and 1 <= forward_rank <= 8:
                    moves.append(chr(new_file) + str(forward_rank))
        
        elif piece_type == 'king':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file, new_rank = file + df, rank + dr
                    if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                        moves.append(chr(new_file) + str(new_rank))
        
        elif piece_type == 'observer':
            # Observer moves like a king
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file, new_rank = file + df, rank + dr
                    if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                        moves.append(chr(new_file) + str(new_rank))
        
        logger.debug(f"Generated {len(moves)} possible moves for {piece_type}")
        return moves
    
    def is_check(self, game_id: str, color: str) -> bool:
        """Check if given color's king is in check"""
        debug_trace(f"Checking if {color} king is in check")
        
        # Find the king's position
        king_position = self._find_king_position(game_id, color)
        if not king_position:
            logger.error(f"Could not find {color} king!")
            return False
        
        # Check if any opponent piece attacks the king's position
        opponent_color = "black" if color == "white" else "white"
        attacking_pieces = self._get_pieces_attacking_square(game_id, king_position, opponent_color)
        
        is_in_check = len(attacking_pieces) > 0
        if is_in_check:
            logger.info(f"{color} king at {king_position} is in check from: {attacking_pieces}")
        else:
            logger.debug(f"{color} king at {king_position} is not in check")
        
        return is_in_check
    
    def is_checkmate(self, game_id: str, color: str) -> bool:
        """Check if given color is in checkmate"""
        debug_trace(f"Checking if {color} is in checkmate")
        
        # First check if king is in check
        if not self.is_check(game_id, color):
            logger.debug(f"{color} king is not in check, so not checkmate")
            return False
        
        # Check if any legal move removes the check
        color_pieces = self._get_all_pieces_for_color(game_id, color)
        
        for piece in color_pieces:
            if piece['captured']:
                continue
                
            piece_moves = self.get_valid_moves(game_id, piece['id'])
            for move in piece_moves['valid_moves']:
                # Temporarily make the move and check if king is still in check
                current_pos = self._get_piece_current_position(piece['id'])
                if not self._would_be_in_check_after_move(game_id, piece['id'], current_pos, move):
                    logger.debug(f"{color} has legal move: {piece['id']} {current_pos} -> {move}")
                    return False
        
        logger.info(f"{color} is in checkmate!")
        return True
    
    def is_stalemate(self, game_id: str, color: str) -> bool:
        """Check if given color is in stalemate"""
        debug_trace(f"Checking if {color} is in stalemate")
        
        # First check that king is NOT in check
        if self.is_check(game_id, color):
            logger.debug(f"{color} king is in check, so not stalemate")
            return False
        
        # Check if any piece has legal moves
        color_pieces = self._get_all_pieces_for_color(game_id, color)
        
        for piece in color_pieces:
            if piece['captured']:
                continue
                
            piece_moves = self.get_valid_moves(game_id, piece['id'])
            if piece_moves['valid_moves']:
                logger.debug(f"{color} has legal moves available, not stalemate")
                return False
        
        logger.info(f"{color} is in stalemate!")
        return True

    def _find_king_position(self, game_id: str, color: str) -> Optional[str]:
        """Find the current position of the king for a given color"""
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (k:Piece {type: 'king', color: $color})-[:BELONGS_TO]->(g)
        MATCH (k)-[:OCCUPIES]->(pos:Position)
        WHERE k.captured = false AND pos.is_ghost = false
        RETURN pos.square AS position
        """
        
        result = self.db.execute_query(query, {'game_id': game_id, 'color': color})
        if result:
            return result[0]['position']
        return None

    def _get_pieces_attacking_square(self, game_id: str, target_square: str, attacking_color: str) -> List[str]:
        """Get all pieces of attacking_color that can attack target_square (including quantum pieces)"""
        attacking_pieces = []
        
        # Get all pieces of the attacking color
        pieces = self._get_all_pieces_for_color(game_id, attacking_color)
        
        for piece in pieces:
            if piece['captured']:
                continue
                
            # For quantum pieces, check all their positions
            positions = self._get_all_piece_positions(piece['id'])
            
            for pos in positions:
                if self._can_piece_attack_square(piece, pos, target_square, game_id):
                    attacking_pieces.append(piece['id'])
                    break  # Only add piece once even if multiple positions can attack
        
        return attacking_pieces

    def _get_all_piece_positions(self, piece_id: str) -> List[str]:
        """Get all positions for a piece (including ghost positions for superposed pieces)"""
        query = """
        MATCH (p:Piece {id: $piece_id})-[:OCCUPIES]->(pos:Position)
        RETURN pos.square AS position, pos.is_ghost AS is_ghost
        """
        
        results = self.db.execute_query(query, {'piece_id': piece_id})
        positions = []
        
        for result in results:
            positions.append(result['position'])
        
        return positions

    def _can_piece_attack_square(self, piece: Dict, from_square: str, target_square: str, game_id: str) -> bool:
        """Check if piece can attack target square (raw move pattern, ignoring check)"""
        piece_type = piece['type']
        
        # Skip king to avoid infinite recursion in check detection
        if piece_type == 'king':
            return self._is_valid_king_move(from_square, target_square)
        
        # Check basic move pattern
        if not self._is_valid_move_pattern(piece_type, from_square, target_square, piece, game_id):
            return False
            
        # Check path is clear (except for knights)
        if piece_type != 'knight':
            if self._is_path_blocked(game_id, from_square, target_square):
                return False
        
        return True

    def _would_be_in_check_after_move(self, game_id: str, piece_id: str, from_square: str, to_square: str) -> bool:
        """Check if making a move would leave own king in check"""
        # Get piece info
        piece_data = self.db.get_piece_state(piece_id)
        if not piece_data:
            return False
            
        color = piece_data['color']
        piece_type = piece_data['type']
        
        # Special case: if moving the king, check if destination is safe
        if piece_type == 'king':
            opponent_color = "black" if color == "white" else "white"
            # Temporarily ignore the king's current position when checking attacks
            attacking_pieces = self._get_pieces_attacking_square_ignore_piece(
                game_id, to_square, opponent_color, piece_id
            )
            return len(attacking_pieces) > 0
        
        # For other pieces, we need to simulate the move more carefully
        # This is a simplified approach - check if the piece was blocking an attack on the king
        king_pos = self._find_king_position(game_id, color)
        if not king_pos:
            return False
        
        # Check if current piece is blocking an attack line to the king
        opponent_color = "black" if color == "white" else "white"
        
        # Get pieces that could potentially attack the king through this square
        for opponent_piece in self._get_all_pieces_for_color(game_id, opponent_color):
            if opponent_piece['captured']:
                continue
                
            opponent_positions = self._get_all_piece_positions(opponent_piece['id'])
            for opp_pos in opponent_positions:
                # Check if opponent piece attacks king through the moving piece's square
                if (self._is_on_attack_line(opp_pos, from_square, king_pos) and
                    self._can_piece_attack_square(opponent_piece, opp_pos, king_pos, game_id)):
                    return True
        
        return False

    def _get_pieces_attacking_square_ignore_piece(
        self, 
        game_id: str, 
        target_square: str, 
        attacking_color: str, 
        ignore_piece_id: str
    ) -> List[str]:
        """Get attacking pieces while ignoring a specific piece (for king move validation)"""
        attacking_pieces = []
        pieces = self._get_all_pieces_for_color(game_id, attacking_color)
        
        for piece in pieces:
            if piece['captured'] or piece['id'] == ignore_piece_id:
                continue
                
            positions = self._get_all_piece_positions(piece['id'])
            for pos in positions:
                if self._can_piece_attack_square(piece, pos, target_square, game_id):
                    attacking_pieces.append(piece['id'])
                    break
        
        return attacking_pieces

    def _is_on_attack_line(self, attacker_pos: str, middle_pos: str, target_pos: str) -> bool:
        """Check if middle_pos is on the attack line from attacker_pos to target_pos"""
        # This is a simplified check for sliding pieces (rook, bishop, queen)
        ax, ay = ord(attacker_pos[0]), int(attacker_pos[1])
        mx, my = ord(middle_pos[0]), int(middle_pos[1])
        tx, ty = ord(target_pos[0]), int(target_pos[1])
        
        # Check if all three points are collinear
        # Vector from attacker to middle
        v1x, v1y = mx - ax, my - ay
        # Vector from attacker to target
        v2x, v2y = tx - ax, ty - ay
        
        # Check if vectors are parallel (cross product = 0)
        cross_product = v1x * v2y - v1y * v2x
        
        if cross_product != 0:
            return False  # Not collinear
        
        # Check if middle is between attacker and target
        if v2x != 0:
            t = v1x / v2x
        elif v2y != 0:
            t = v1y / v2y
        else:
            return False  # Degenerate case
        
        return 0 < t < 1

    def _get_all_pieces_for_color(self, game_id: str, color: str) -> List[Dict]:
        """Get all pieces for a given color"""
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece {color: $color})-[:BELONGS_TO]->(g)
        RETURN p AS piece
        """
        
        results = self.db.execute_query(query, {'game_id': game_id, 'color': color})
        return [dict(result['piece']) for result in results]

    def _get_piece_current_position(self, piece_id: str) -> Optional[str]:
        """Get current (non-ghost) position of a piece"""
        query = """
        MATCH (p:Piece {id: $piece_id})-[:OCCUPIES]->(pos:Position)
        WHERE pos.is_ghost = false
        RETURN pos.square AS position
        """
        
        result = self.db.execute_query(query, {'piece_id': piece_id})
        if result:
            return result[0]['position']
        return None

    def _is_valid_king_move(self, from_square: str, to_square: str) -> bool:
        """Check if move is valid for king (one square in any direction)"""
        from_file, from_rank = ord(from_square[0]), int(from_square[1])
        to_file, to_rank = ord(to_square[0]), int(to_square[1])
        
        file_diff = abs(to_file - from_file)
        rank_diff = abs(to_rank - from_rank)
        
        return file_diff <= 1 and rank_diff <= 1 and (file_diff != 0 or rank_diff != 0)
