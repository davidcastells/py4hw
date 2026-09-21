import py4hw
import math

class CreditBasedFlowControl(py4hw.Logic):
    def __init__(self, parent, name, in_ready, in_valid, in_value, credit_inc, credits,
                 out_ready, out_valid, out_value, maxcredits=4):
        '''
        SUMMARY.
        Credit-based flow control with an internal registered skid buffer.

        The data path in_value -> out_value goes entirely through a register:
        out_value/out_valid are driven only from that register, never
        combinationally from in_value/in_valid. This costs one cycle of
        latency but removes the combinational data path, and still allows
        back-to-back transfers at full throughput (the register can be
        reloaded the same cycle it is drained).

        Credits are consumed at ACCEPTANCE (in_valid & in_ready), not at
        output firing (out_valid & out_ready). This means in_ready drops
        exactly one cycle after an admitted transaction consumes the last
        credit -- the minimum possible latency for a registered counter --
        and it is not possible for a second transaction to be admitted on
        the same credit, even though the skid buffer can still accept a
        new item the same cycle it drains an old one (for throughput)
        when credits allow it.

        Note: in_ready still combinationally depends on out_ready (and on
        the buffer's occupancy). That dependency is inherent to any
        single-register elastic buffer that wants to sustain full
        throughput; it cannot be removed without either adding a second
        buffer stage (2-deep skid buffer) or accepting a throughput bubble
        every other transfer.

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.
        name : TYPE
            DESCRIPTION.
        in_ready : Wire
            Ready signal driven back to the producer.
        in_valid : Wire
            Valid signal from the producer.
        in_value : Wire
            Data input from the producer, latched into the skid buffer
            on acceptance.
        credit_inc : Wire
            Credit increment input.
        credits : Wire
            Current credit count (registered, output). Decremented on
            acceptance (in_valid & in_ready), incremented on credit_inc.
        out_ready : Wire
            Ready signal from the consumer.
        out_valid : Wire
            Valid signal to the consumer, driven from the skid buffer's
            occupancy register.
        out_value : Wire
            Data output to the consumer, driven from the skid buffer's
            data register. Guaranteed stable whenever out_valid=1, since
            it is purely registered with no combinational path from
            in_value.
        maxcredits : TYPE, optional
            DESCRIPTION. The default is 4.

        Returns
        -------
        None
        '''
        super().__init__(parent, name)

        self.addIn('in_valid', in_valid)
        self.addOut('in_ready', in_ready)
        self.addIn('in_value', in_value)

        self.addIn('out_ready', out_ready)
        self.addOut('out_valid', out_valid)
        self.addOut('out_value', out_value)

        self.addIn('credit_inc', credit_inc)
        self.addOut('credits', credits)

        w = int(math.ceil(math.log2(maxcredits))) + 1
        assert (credits.getWidth() >= w)

        # --- skid buffer occupancy (needed to compute in_ready/accept first) ---
        buf_valid = self.wire('buf_valid')
        n_buf_valid = self.wire('n_buf_valid')
        can_accept = self.wire('can_accept')
        iszero = self.wire('iszero')
        nonzero = self.wire('nonzero')
        accept = self.wire('accept')
        not_draining = self.wire('not_draining')
        hold = self.wire('hold')
        next_buf_valid = self.wire('next_buf_valid')

        py4hw.EqualConstant(self, 'iszero', credits, 0, iszero)
        py4hw.Not(self, 'nonzero', iszero, nonzero)

        # can accept new data if there are credits AND
        # (the buffer is empty OR it is being drained this same cycle)
        py4hw.Not(self, 'n_buf_valid', buf_valid, n_buf_valid)
        py4hw.Or2(self, 'empty_or_draining', n_buf_valid, out_ready, can_accept)
        py4hw.And2(self, 'in_ready_calc', can_accept, nonzero, in_ready)

        py4hw.And2(self, 'accept', in_valid, in_ready, accept)

        # next_buf_valid = accept | (buf_valid & ~out_ready)
        py4hw.Not(self, 'not_draining', out_ready, not_draining)
        py4hw.And2(self, 'hold_valid', buf_valid, not_draining, hold)
        py4hw.Or2(self, 'next_buf_valid', accept, hold, next_buf_valid)

        py4hw.Reg(self, 'buf_valid_reg', d=next_buf_valid, q=buf_valid)
        py4hw.Reg(self, 'buf_value_reg', d=in_value, q=out_value, enable=accept)

        py4hw.Buf(self, 'out_valid_buf', buf_valid, out_valid)

        # --- credit counter: decrement on ACCEPT, not on output fire ---
        added = self.wire('added', w)
        next_credit = self.wire('next_credit', w)

        py4hw.Add(self, 'add', credits, credit_inc, added)
        py4hw.Sub(self, 'sub', added, accept, next_credit)
        py4hw.Reg(self, 'credit', d=next_credit, q=credits)