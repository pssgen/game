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
        if not self._is_valid_move_pattern(piece_type, from_square, to_square, piece_data):
            logger.debug(f"Invalid move pattern for {piece_type}: {from_square} -> {to_square}")
            return False, f"Invalid move pattern for {piece_type}"
        
        # Check path obstruction (except knights)
        if piece_type != 'knight':
            if self._is_path_blocked(game_id, from_square, to_square):
                logger.debug(f"Path blocked for move: {from_square} -> {to_square}")
                return False, "Path is blocked"
        
        # TODO: Check if move puts/leaves own king in check
        
        logger.debug(f"Move validated successfully: {piece_id} {from_square} -> {to_square}")
        return True, None
    
    def _is_valid_move_pattern(
        self,
        piece_type: str,
        from_square: str,
        to_square: str,
        piece_data: Dict
    ) -> bool:
        """Validate move pattern for piece type"""
        debug_trace(f"Validating move pattern for {piece_type}: {from_square} -> {to_square}")
        
        from_file, from_rank = ord(from_square[0]), int(from_square[1])
        to_file, to_rank = ord(to_square[0]), int(to_square[1])
        
        file_diff = abs(to_file - from_file)
        rank_diff = abs(to_rank - from_rank)
        
        if piece_type == 'pawn':
            return self._is_valid_pawn_move(from_square, to_square, piece_data)
        
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
        
        logger.debug(f"Unknown piece type: {piece_type}")
        return False
    
    def _is_valid_pawn_move(
        self,
        from_square: str,
        to_square: str,
        piece_data: Dict
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
            # TODO: Check if target square has enemy piece
            logger.debug("Valid pawn capture move")
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
        
        logger.debug(f"Generated {len(moves)} possible moves for {piece_type}")
        return moves
    
    def is_check(self, game_id: str, color: str) -> bool:
        """Check if given color's king is in check"""
        debug_trace(f"Checking if {color} king is in check")
        
        # TODO: Implement check detection
        # This requires checking all opponent pieces' valid moves
        # to see if any attack the king's position
        logger.debug(f"Check detection not yet implemented for {color}")
        return False
    
    def is_checkmate(self, game_id: str, color: str) -> bool:
        """Check if given color is in checkmate"""
        debug_trace(f"Checking if {color} is in checkmate")
        
        # TODO: Implement checkmate detection
        # King in check + no legal moves that remove check
        logger.debug(f"Checkmate detection not yet implemented for {color}")
        return False
    
    def is_stalemate(self, game_id: str, color: str) -> bool:
        """Check if given color is in stalemate"""
        debug_trace(f"Checking if {color} is in stalemate")
        
        # TODO: Implement stalemate detection
        # King not in check + no legal moves available
        logger.debug(f"Stalemate detection not yet implemented for {color}")
        return False
